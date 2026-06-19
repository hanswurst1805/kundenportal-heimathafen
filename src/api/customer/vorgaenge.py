from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.schemas.angebot import AngebotOut
from src.schemas.auftrag import AuftragOut, AuftragsbestaetigungOut
from src.schemas.avv import AVVOut
from src.schemas.leistungsschein import LeistungsscheinKundenSicht
from src.schemas.signatur import OffeneSignaturOut
from src.schemas.vorgang import VorgangDetailOut, VorgangOut
from src.services.vorgang import VorgangDaten, get_vorgang, list_vorgaenge

router = APIRouter(prefix="/vorgaenge", tags=["portal-vorgaenge"])

_SIGNATUR_LABEL = {
    "angebot": "Angebot",
    "avv": "Auftragsverarbeitungsvertrag",
    "bestellung": "Bestellung",
    "auftragsbestaetigung": "Auftragsbestätigung",
}


def _zu_out(v: VorgangDaten) -> VorgangOut:
    offen = v.offene_signaturen[0] if v.offene_signaturen else None
    return VorgangOut(
        typ=v.typ,
        root_id=v.root_id,
        referenz=v.referenz,
        titel=v.titel,
        status_kunde=v.status_kunde,
        created_at=v.created_at,
        angebot_id=v.angebot.id if v.angebot else None,
        avv_id=v.avv.id if v.avv else None,
        auftrag_id=v.auftrag.id if v.auftrag else None,
        leistungsschein_id=v.leistungsschein.id if v.leistungsschein else None,
        auftragsbestaetigung_vorhanden=v.auftragsbestaetigung is not None,
        offene_signatur_token=offen.token if offen else None,
    )


@router.get("", response_model=list[VorgangOut])
async def liste(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    vorgaenge = await list_vorgaenge(session, ctx.customer_id)
    return [_zu_out(v) for v in vorgaenge]


@router.get("/{typ}/{root_id}", response_model=VorgangDetailOut)
async def detail(
    typ: str,
    root_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    v = await get_vorgang(session, ctx.customer_id, typ, root_id)
    if not v:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vorgang nicht gefunden")

    basis = _zu_out(v)
    return VorgangDetailOut(
        **basis.model_dump(),
        angebot=AngebotOut.model_validate(v.angebot) if v.angebot else None,
        avv=AVVOut.model_validate(v.avv) if v.avv else None,
        auftrag=AuftragOut.model_validate(v.auftrag) if v.auftrag else None,
        auftragsbestaetigung=(
            AuftragsbestaetigungOut.model_validate(v.auftragsbestaetigung)
            if v.auftragsbestaetigung
            else None
        ),
        leistungsschein=(
            LeistungsscheinKundenSicht.model_validate(v.leistungsschein) if v.leistungsschein else None
        ),
        offene_signaturen=[
            OffeneSignaturOut(
                id=s.id,
                bezugstyp=s.bezugstyp,
                token=s.token,
                status=s.status,
                titel=_SIGNATUR_LABEL.get(s.bezugstyp, s.bezugstyp),
            )
            for s in v.offene_signaturen
        ],
    )
