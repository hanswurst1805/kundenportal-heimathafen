"""Login, Zwei-Faktor-Authentifizierung und Self-Service-Endpunkte."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    AuthContext,
    consume_backup_code,
    create_access_token,
    create_mfa_token,
    decode_mfa_token,
    generate_backup_codes,
    generate_totp_secret,
    get_current_user,
    hash_backup_codes,
    hash_password,
    totp_provisioning_uri,
    totp_qr_data_uri,
    verify_password,
    verify_totp_code,
)
from src.core.database import get_session
from src.models.user import User
from src.schemas.auth import (
    ChangePasswordRequest,
    LoginResponse,
    MFAVerifyRequest,
    TOTPDisableRequest,
    TOTPEnableRequest,
    TOTPEnableResponse,
    TOTPSetupResponse,
    UserMeResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    result = await session.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzername oder Passwort ist falsch")

    if user.totp_enabled:
        return LoginResponse(mfa_required=True, mfa_token=create_mfa_token(user.id))

    return LoginResponse(
        access_token=create_access_token(user.id, user.role, user.customer_id),
        token_type="bearer",
        needs_2fa_setup=user.totp_required and not user.totp_enabled,
    )


@router.post("/2fa/verify", response_model=LoginResponse)
async def verify_2fa(
    payload: MFAVerifyRequest,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    user_id = decode_mfa_token(payload.mfa_token)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA-Token ist ungueltig oder abgelaufen")

    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzer nicht gefunden")

    if user.totp_secret and verify_totp_code(user.totp_secret, payload.code):
        pass
    elif user.backup_codes:
        remaining = consume_backup_code(user.backup_codes, payload.code)
        if remaining is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Code ist ungueltig")
        user.backup_codes = remaining
        await session.flush()
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Code ist ungueltig")

    return LoginResponse(
        access_token=create_access_token(user.id, user.role, user.customer_id),
        token_type="bearer",
    )


@router.get("/me", response_model=UserMeResponse)
async def me(
    ctx: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserMeResponse:
    user = await session.get(User, ctx.user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benutzer nicht gefunden")
    return UserMeResponse.model_validate(user)


@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    ctx: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TOTPSetupResponse:
    user = await session.get(User, ctx.user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benutzer nicht gefunden")
    if user.totp_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "2FA ist bereits aktiviert")

    secret = generate_totp_secret()
    user.totp_secret = secret
    await session.flush()
    provisioning_uri = totp_provisioning_uri(secret, user.username)
    return TOTPSetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_code=totp_qr_data_uri(provisioning_uri),
    )


@router.post("/2fa/enable", response_model=TOTPEnableResponse)
async def enable_2fa(
    payload: TOTPEnableRequest,
    ctx: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TOTPEnableResponse:
    user = await session.get(User, ctx.user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benutzer nicht gefunden")
    if not user.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "2FA-Setup wurde noch nicht gestartet")
    if not verify_totp_code(user.totp_secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code ist ungueltig")

    backup_codes = generate_backup_codes()
    user.totp_enabled = True
    user.backup_codes = hash_backup_codes(backup_codes)
    await session.flush()
    return TOTPEnableResponse(backup_codes=backup_codes)


@router.post("/2fa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_2fa(
    payload: TOTPDisableRequest,
    ctx: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    user = await session.get(User, ctx.user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benutzer nicht gefunden")
    if user.totp_required:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Zwei-Faktor-Authentifizierung kann fuer diese Rolle nicht deaktiviert werden"
        )
    if not user.totp_secret or not verify_totp_code(user.totp_secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code ist ungueltig")

    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    await session.flush()


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    ctx: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    user = await session.get(User, ctx.user_id)
    if not user or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Aktuelles Passwort ist falsch")
    user.password_hash = hash_password(payload.new_password)
    await session.flush()
