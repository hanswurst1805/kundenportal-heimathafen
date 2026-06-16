from __future__ import annotations

import uuid

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_signature_provider_by_name
from src.automation.events import publish
from src.core.auth import AuthContext, require_customer
from src.core.config import settings
from src.core.database import get_session
from src.models.customer import Customer
from src.models.ereignis import AKTEUR_USER
from src.models.signatur import (
    SIGNATUR_ERSTELLT,
    SIGNATUR_SIGNIERT,
    SIGNATUR_VERSENDET,
    Signaturvorgang,
)
from src.core.status_codes import EVENT_SIGNATURE_COMPLETED
from src.schemas.signatur import OffeneSignaturOut, SignaturInput, SignaturvorgangOut
from src.services.pdf_signing import build_vorschau_pdf
from src.services.signatur_resolve import (
    build_dokument_inhalt,
    resolve_customer_id,
    resolve_titel,
)
from datetime import datetime, timezone

router = APIRouter(prefix="/signatur", tags=["portal-signatur"])


@router.get("", response_model=list[OffeneSignaturOut])
async def list_offene_signaturen(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    """Alle offenen Signaturvorgaenge des eingeloggten Kunden (zum Signieren)."""
    vorgaenge = (
        await session.execute(
            select(Signaturvorgang)
            .where(Signaturvorgang.status.in_([SIGNATUR_ERSTELLT, SIGNATUR_VERSENDET]))
            .order_by(Signaturvorgang.created_at.desc())
        )
    ).scalars().all()

    offen: list[OffeneSignaturOut] = []
    for vorgang in vorgaenge:
        customer_id = await resolve_customer_id(session, vorgang)
        if customer_id != ctx.customer_id:
            continue
        offen.append(
            OffeneSignaturOut(
                id=vorgang.id,
                bezugstyp=vorgang.bezugstyp,
                token=vorgang.token,
                status=vorgang.status,
                titel=await resolve_titel(session, vorgang),
            )
        )
    return offen


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


@router.get("/{token}/vorschau")
async def vorschau(
    token: str,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    """Unsigniertes Vorschau-PDF des zu signierenden Dokuments."""
    vorgang = (
        await session.execute(select(Signaturvorgang).where(Signaturvorgang.token == token))
    ).scalar_one_or_none()
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    customer_id = await resolve_customer_id(session, vorgang)
    if customer_id:
        ctx.require_customer_scope(customer_id)
    if customer_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    inhalt = await build_dokument_inhalt(session, vorgang, customer_id)
    pdf = await asyncio.to_thread(build_vorschau_pdf, inhalt)
    return Response(content=pdf, media_type="application/pdf")


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

    # Entscheidung pro Vorgang (nicht global): ein als inhouse angelegter Vorgang
    # verlangt eine handschriftliche Unterschrift – ein stub-Vorgang bleibt
    # Klick-Signatur, auch wenn die globale Einstellung inzwischen wechselte.
    anbieter = vorgang.anbieter or settings.signature_provider
    if anbieter == "inhouse" and not payload.signatur_bild:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unterschrift fehlt")

    # Unterzeichnername bestimmen: Eingabe -> Kundenkontakt -> Benutzername.
    unterzeichner_name = payload.unterzeichner_name
    if not unterzeichner_name and customer_id:
        customer = await session.get(Customer, customer_id)
        unterzeichner_name = customer.contact_name or customer.name if customer else None
    unterzeichner_name = unterzeichner_name or ctx.username

    await get_signature_provider_by_name(anbieter).apply_signature(
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
