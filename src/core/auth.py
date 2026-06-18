"""JWT + bcrypt + TOTP-2FA Authentifizierung, Rollen- und Mandanten-Kontext."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.models.user import ROLE_ADMIN, ROLE_KUNDE, ROLE_USER, User

# ---------------------------------------------------------------------------
# Krypto-Helpers
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID, role: str, customer_id: Optional[uuid.UUID]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    return jwt.encode(
        {
            "sub": str(user_id),
            "role": role,
            "customer_id": str(customer_id) if customer_id else None,
            "exp": expire,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Zwei-Faktor-Authentifizierung (TOTP)
# ---------------------------------------------------------------------------

MFA_TOKEN_EXPIRE_MINUTES = 5
BACKUP_CODE_COUNT = 10


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, username: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Kundenportal Heimathafen")


def totp_qr_data_uri(provisioning_uri: str) -> str:
    """Rendert die otpauth-URI als scanbaren QR-Code und gibt ihn als
    SVG-Data-URI (base64) zurueck, der direkt in ein <img>-Tag passt.

    Bewusst die reine-Python-SVG-Factory (stdlib ElementTree) – so wird keine
    zusaetzliche Bild-Bibliothek (Pillow/pypng) benoetigt."""
    import base64
    import io

    import qrcode
    import qrcode.image.svg

    img = qrcode.make(provisioning_uri, image_factory=qrcode.image.svg.SvgImage)
    buffer = io.BytesIO()
    img.save(buffer)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.totp.TOTP(secret).verify(code.strip().replace(" ", ""), valid_window=1)


def generate_backup_codes() -> list[str]:
    """Gibt Klartext-Backup-Codes zurueck (z.B. 'ab12-cd34')."""
    return [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(BACKUP_CODE_COUNT)]


def hash_backup_codes(codes: list[str]) -> list[str]:
    return [hash_password(c) for c in codes]


def consume_backup_code(hashed_codes: list[str], code: str) -> Optional[list[str]]:
    """Prueft den Code gegen die gehashten Backup-Codes. Bei Treffer wird eine
    aktualisierte Liste (ohne den verbrauchten Code) zurueckgegeben, sonst None."""
    code = code.strip().lower()
    for h in hashed_codes:
        if verify_password(code, h):
            return [x for x in hashed_codes if x != h]
    return None


def create_mfa_token(user_id: uuid.UUID) -> str:
    """Kurzlebiges Token zwischen Passwort- und 2FA-Code-Pruefung."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "scope": "2fa", "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_mfa_token(token: str) -> Optional[uuid.UUID]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
    if payload.get("scope") != "2fa":
        return None
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Auth-Kontext
# ---------------------------------------------------------------------------


class AuthContext(BaseModel):
    user_id: uuid.UUID
    username: str
    role: str  # admin | user | kunde
    customer_id: Optional[uuid.UUID] = None
    totp_enabled: bool = False
    totp_required: bool = False

    @property
    def is_internal(self) -> bool:
        return self.role in (ROLE_ADMIN, ROLE_USER)

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def needs_2fa_setup(self) -> bool:
        # Erzwingung nur, wenn 2FA global Pflicht ist (sonst optional).
        return settings.require_2fa and self.totp_required and not self.totp_enabled

    def require_customer_scope(self, target_customer_id: uuid.UUID) -> None:
        """Wirft 404, falls ein Kunde auf Daten eines anderen Mandanten zugreift.

        Interne Rollen (admin/user) sind nicht eingeschraenkt."""
        if self.is_internal:
            return
        if self.customer_id != target_customer_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")


# ---------------------------------------------------------------------------
# FastAPI Security Scheme + Dependencies
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def _user_from_jwt(token: str, session: AsyncSession) -> Optional[AuthContext]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        return None
    return AuthContext(
        user_id=user.id,
        username=user.username,
        role=user.role,
        customer_id=user.customer_id,
        totp_enabled=user.totp_enabled,
        totp_required=user.totp_required,
    )


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> AuthContext:
    """FastAPI-Dependency: liefert AuthContext oder 401."""
    if token:
        ctx = await _user_from_jwt(token, session)
        if ctx:
            return ctx
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nicht authentifiziert",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_internal(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not ctx.is_internal:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Interner Zugriff erforderlich")
    if ctx.needs_2fa_setup:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Zwei-Faktor-Authentifizierung muss zuerst eingerichtet werden",
        )
    return ctx


def require_admin(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not ctx.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin-Rechte erforderlich")
    if ctx.needs_2fa_setup:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Zwei-Faktor-Authentifizierung muss zuerst eingerichtet werden",
        )
    return ctx


def require_customer(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
    if ctx.role != ROLE_KUNDE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Kundenzugriff erforderlich")
    return ctx


def require_role(*roles: str):
    def _checker(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
        if ctx.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Keine Berechtigung")
        if ctx.role in (ROLE_ADMIN, ROLE_USER) and ctx.needs_2fa_setup:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Zwei-Faktor-Authentifizierung muss zuerst eingerichtet werden",
            )
        return ctx

    return _checker
