from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_signature_provider
from src.automation.events import publish
from src.core.auth import AuthContext, require_customer
from src.core.config import settings
from src.core.database import get_session
from src.models.customer import Customer
from src.models.ereignis import AKTEUR_USER
from src.models.signatur import SIGNATUR_SIGNIERT, SIGNATUR_VERSENDET, Signaturvorgang
from src.core.status_codes import EVENT_SIGNATURE_COMPLETED
from src.schemas.signatur import SignaturInput, SignaturvorgangOut
from src.services.signatur_resolve import resolve_customer_id
from datetime import datetime, timezone

router = APIRouter(prefix="/signatur", tags=["portal-signatur"])


@router.get("/by-bezug/{bezugstyp}/{bezugs_id}", response_model=list[SignaturvorgangOut])
async def list_signaturvorgaenge_fuer_bezug(
    bezugstyp: str,
    bezugs_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    vorgaenge = (
        await session.execute(
            select(Signaturvorgang)
            .where(Signaturvorgang.bezugstyp == bezugstyp, Signaturvorgang.bezugs_id == bezugs_id)
            .order_by(Signaturvorgang.created_at.desc())
        )
    ).scalars().all()
    if vorgaenge:
        customer_id = await resolve_customer_id(session, vorgaenge[0])
        if customer_id:
            ctx.require_customer_scope(customer_id)
    return vorgaenge


@router.get("/{token}", response_model=SignaturvorgangOut)
async def get_signaturvorgang(
    token: str,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    vorgang = (
        await session.execute(select(Signaturvorgang).where(Signaturvorgang.token == token))
    ).scalar_one_or_none()
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    customer_id = await resolve_customer_id(session, vorgang)
    if customer_id:
        ctx.require_customer_scope(customer_id)
    return vorgang


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/{token}/signieren", response_model=SignaturvorgangOut)
async def signieren(
    token: str,
    request: Request,
    payload: SignaturInput | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    vorgang = (
        await session.execute(select(Signaturvorgang).where(Signaturvorgang.token == token))
    ).scalar_one_or_none()
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if vorgang.status != SIGNATUR_VERSENDET:
        raise HTTPException(status.HTTP_409_CONFLICT, "Signaturvorgang ist nicht offen")

    customer_id = await resolve_customer_id(session, vorgang)
    if customer_id:
        ctx.require_customer_scope(customer_id)

    payload = payload or SignaturInput()

    # Beim inhouse-Provider ist eine handschriftliche Unterschrift erforderlich.
    if settings.signature_provider == "inhouse" and not payload.signatur_bild:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unterschrift fehlt")

    # Unterzeichnername bestimmen: Eingabe -> Kundenkontakt -> Benutzername.
    unterzeichner_name = payload.unterzeichner_name
    if not unterzeichner_name and customer_id:
        customer = await session.get(Customer, customer_id)
        unterzeichner_name = customer.contact_name or customer.name if customer else None
    unterzeichner_name = unterzeichner_name or ctx.username

    await get_signature_provider().apply_signature(
        session,
        vorgang,
        unterzeichner_name=unterzeichner_name,
        signatur_bild=payload.signatur_bild,
        ip_adresse=_client_ip(request),
    )

    vorgang.status = SIGNATUR_SIGNIERT
    vorgang.signierzeit = datetime.now(timezone.utc)

    await publish(
        session,
        EVENT_SIGNATURE_COMPLETED,
        customer_id=customer_id,
        bezugstyp=vorgang.bezugstyp,
        bezugs_id=vorgang.bezugs_id,
        akteur_id=ctx.user_id,
        akteur_typ=AKTEUR_USER,
    )

    return vorgang
