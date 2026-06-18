from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.registry import get_signature_provider
from src.core.auth import require_role
from src.core.database import get_session
from src.models.angebot import ANGEBOT_BEREITGESTELLT, ANGEBOT_ENTWURF, Angebot, AngebotPosition
from src.models.dokument import DOK_ANGEBOT, SICHTBAR_INTERN, SICHTBAR_KUNDE, Dokument
from src.models.signatur import BEZUG_ANGEBOT
from src.schemas.angebot import AngebotOut, AngebotUpdate
from src.services.numbering import next_number
from src.services.origin import find_origin_for_angebot, set_origin_status
from src.services.pdf_signing import documents_dir

router = APIRouter(prefix="/angebote", tags=["intern-angebote"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[AngebotOut])
async def list_angebote(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).options(selectinload(Angebot.positionen)).order_by(Angebot.created_at.desc())
    )
    return result.scalars().all()


@router.post("/upload", response_model=AngebotOut, status_code=status.HTTP_201_CREATED)
async def upload_externes_angebot(
    customer_id: uuid.UUID = Form(...),
    titel: str = Form(...),
    gueltig_bis: Optional[date] = Form(None),
    positionen: str = Form("[]"),
    datei: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Legt ein Angebot aus einem extern erstellten PDF an: speichert die Datei
    als (zunaechst internes) Dokument und verknuepft die Positionen optional mit
    Katalog-Leistungen (`leistung_id`)."""
    try:
        roh_positionen = json.loads(positionen)
        if not isinstance(roh_positionen, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Positionen müssen eine JSON-Liste sein")

    angebotsnummer = await next_number(session, Angebot, "ANG")
    angebot = Angebot(
        angebotsnummer=angebotsnummer,
        customer_id=customer_id,
        titel=titel,
        gueltig_bis=gueltig_bis,
    )
    session.add(angebot)
    await session.flush()

    gesamtpreis = Decimal("0")
    for i, pos in enumerate(roh_positionen):
        menge = Decimal(str(pos.get("menge", "1")))
        einzelpreis = Decimal(str(pos.get("einzelpreis", "0")))
        positionspreis = menge * einzelpreis
        leistung_id = pos.get("leistung_id")
        session.add(
            AngebotPosition(
                angebot_id=angebot.id,
                bezeichnung=pos.get("bezeichnung", ""),
                menge=menge,
                einzelpreis=einzelpreis,
                gesamtpreis=positionspreis,
                sort_order=int(pos.get("sort_order", i)),
                leistung_id=uuid.UUID(leistung_id) if leistung_id else None,
            )
        )
        gesamtpreis += positionspreis
    angebot.gesamtpreis = gesamtpreis

    # PDF ablegen (zunaechst nur intern sichtbar – wird beim Bereitstellen freigegeben).
    inhalt = await datei.read()
    sicherer_name = (datei.filename or "angebot.pdf").replace("/", "_").replace("\\", "_")
    ablage = documents_dir() / f"angebot-{angebot.id}-{sicherer_name}"
    ablage.write_bytes(inhalt)
    session.add(
        Dokument(
            customer_id=customer_id,
            typ=DOK_ANGEBOT,
            version=1,
            sichtbarkeit=SICHTBAR_INTERN,
            dateiname=sicherer_name,
            ablageort=str(ablage.resolve()),
            bezugstyp="angebot",
            bezugs_id=angebot.id,
        )
    )

    await session.flush()
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot.id).options(selectinload(Angebot.positionen))
    )
    return result.scalar_one()


@router.get("/{angebot_id}", response_model=AngebotOut)
async def get_angebot(angebot_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
    )
    angebot = result.scalar_one_or_none()
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return angebot


@router.patch("/{angebot_id}", response_model=AngebotOut)
async def update_angebot(
    angebot_id: uuid.UUID, data: AngebotUpdate, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
    )
    angebot = result.scalar_one_or_none()
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if angebot.status != ANGEBOT_ENTWURF:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur Entwürfe können bearbeitet werden")

    if data.titel is not None:
        angebot.titel = data.titel
    if data.gueltig_bis is not None:
        angebot.gueltig_bis = data.gueltig_bis

    if data.positionen is not None:
        angebot.positionen.clear()
        gesamtpreis = Decimal("0")
        for pos in data.positionen:
            positionspreis = pos.menge * pos.einzelpreis
            angebot.positionen.append(
                AngebotPosition(
                    bezeichnung=pos.bezeichnung,
                    menge=pos.menge,
                    einzelpreis=pos.einzelpreis,
                    gesamtpreis=positionspreis,
                    sort_order=pos.sort_order,
                    leistung_id=pos.leistung_id,
                )
            )
            gesamtpreis += positionspreis
        angebot.gesamtpreis = gesamtpreis

    await session.flush()
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot.id).options(selectinload(Angebot.positionen))
    )
    return result.scalar_one()


@router.post("/{angebot_id}/bereitstellen", response_model=AngebotOut)
async def bereitstellen(angebot_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
    )
    angebot = result.scalar_one_or_none()
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if angebot.status != ANGEBOT_ENTWURF:
        raise HTTPException(status.HTTP_409_CONFLICT, "Angebot kann in diesem Status nicht bereitgestellt werden")

    angebot.status = ANGEBOT_BEREITGESTELLT

    # Ein hochgeladenes (extern erstelltes) Angebot-PDF wird jetzt kundensichtbar.
    await session.execute(
        update(Dokument)
        .where(
            Dokument.bezugstyp == "angebot",
            Dokument.bezugs_id == angebot.id,
            Dokument.sichtbarkeit == SICHTBAR_INTERN,
        )
        .values(sichtbarkeit=SICHTBAR_KUNDE)
    )

    origin = await find_origin_for_angebot(session, angebot)
    if origin:
        set_origin_status(origin, "warten_auf_signatur")

    await get_signature_provider().create_envelope(session, BEZUG_ANGEBOT, angebot.id, angebot.titel)

    return angebot
