from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.automation.events import publish
from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.ereignis import AKTEUR_USER
from src.models.signatur import SIGNATUR_SIGNIERT, SIGNATUR_VERSENDET, Signaturvorgang
from src.core.status_codes import EVENT_SIGNATURE_COMPLETED
from src.schemas.signatur import SignaturvorgangOut
from src.services.signatur_resolve import resolve_customer_id
from datetime import datetime, timezone

router = APIRouter(prefix="/signatur", tags=["portal-signatur"])


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


@router.post("/{token}/signieren", response_model=SignaturvorgangOut)
async def signieren(
    token: str,
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
