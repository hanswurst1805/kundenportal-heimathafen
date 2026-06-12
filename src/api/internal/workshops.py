from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.automation.events import publish
from src.core.auth import AuthContext, require_role
from src.core.status_codes import EVENT_KICKOFF_SCHEDULED, EVENT_ONBOARDING_WORKSHOP_FINISHED, EVENT_ONBOARDING_WORKSHOP_SCHEDULED
from src.core.database import get_session
from src.models.ereignis import AKTEUR_USER
from src.models.leistungsschein import (
    WORKSHOP_PROTOKOLL_FREIGEGEBEN,
    WORKSHOP_TYP_KICKOFF,
    WORKSHOP_TYP_ONBOARDING,
    Leistungsschein,
    Workshop,
)
from src.schemas.leistungsschein import WorkshopCreate, WorkshopOut, WorkshopUpdate

router = APIRouter(
    prefix="/leistungsscheine/{leistungsschein_id}/workshops",
    tags=["intern-workshops"],
    dependencies=[Depends(require_role("user", "admin"))],
)


@router.get("", response_model=list[WorkshopOut])
async def list_workshops(leistungsschein_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Workshop).where(Workshop.leistungsschein_id == leistungsschein_id))
    return result.scalars().all()


@router.post("", response_model=WorkshopOut, status_code=status.HTTP_201_CREATED)
async def create_workshop(
    leistungsschein_id: uuid.UUID,
    data: WorkshopCreate,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_role("user", "admin")),
):
    ls = await session.get(Leistungsschein, leistungsschein_id)
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    workshop = Workshop(leistungsschein_id=ls.id, **data.model_dump())
    session.add(workshop)
    await session.flush()

    if workshop.typ == WORKSHOP_TYP_KICKOFF:
        ereignis_typ = EVENT_KICKOFF_SCHEDULED
    elif workshop.typ == WORKSHOP_TYP_ONBOARDING:
        ereignis_typ = EVENT_ONBOARDING_WORKSHOP_SCHEDULED
    else:
        ereignis_typ = None

    if ereignis_typ:
        await publish(
            session,
            ereignis_typ,
            customer_id=ls.customer_id,
            bezugstyp="leistungsschein",
            bezugs_id=ls.id,
            akteur_id=ctx.user_id,
            akteur_typ=AKTEUR_USER,
            payload={"workshop_id": str(workshop.id)},
        )

    return workshop


@router.patch("/{workshop_id}", response_model=WorkshopOut)
async def update_workshop(
    leistungsschein_id: uuid.UUID,
    workshop_id: uuid.UUID,
    data: WorkshopUpdate,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_role("user", "admin")),
):
    workshop = await session.get(Workshop, workshop_id)
    if not workshop or workshop.leistungsschein_id != leistungsschein_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    vorher_status = workshop.status
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(workshop, field, value)

    if (
        workshop.typ == WORKSHOP_TYP_ONBOARDING
        and vorher_status != WORKSHOP_PROTOKOLL_FREIGEGEBEN
        and workshop.status == WORKSHOP_PROTOKOLL_FREIGEGEBEN
    ):
        ls = await session.get(Leistungsschein, leistungsschein_id)
        await publish(
            session,
            EVENT_ONBOARDING_WORKSHOP_FINISHED,
            customer_id=ls.customer_id,
            bezugstyp="leistungsschein",
            bezugs_id=ls.id,
            akteur_id=ctx.user_id,
            akteur_typ=AKTEUR_USER,
            payload={"workshop_id": str(workshop.id)},
        )

    return workshop
