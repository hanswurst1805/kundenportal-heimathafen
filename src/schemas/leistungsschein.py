from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class AufgabeOut(BaseModel):
    id: uuid.UUID
    titel: str
    beschreibung: Optional[str] = None
    zustaendigkeit_id: Optional[uuid.UUID] = None
    faelligkeit: Optional[date] = None
    status: str
    sort_order: int

    model_config = {"from_attributes": True}


class AufgabeCreate(BaseModel):
    titel: str
    beschreibung: Optional[str] = None
    zustaendigkeit_id: Optional[uuid.UUID] = None
    faelligkeit: Optional[date] = None
    sort_order: int = 0


class AufgabeUpdate(BaseModel):
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    zustaendigkeit_id: Optional[uuid.UUID] = None
    faelligkeit: Optional[date] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class WorkshopOut(BaseModel):
    id: uuid.UUID
    typ: str
    termin: Optional[datetime] = None
    teilnehmer: Optional[list[Any]] = None
    protokoll: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class WorkshopCreate(BaseModel):
    typ: str
    termin: Optional[datetime] = None
    teilnehmer: Optional[list[Any]] = None


class WorkshopUpdate(BaseModel):
    termin: Optional[datetime] = None
    teilnehmer: Optional[list[Any]] = None
    protokoll: Optional[str] = None
    status: Optional[str] = None


class LeistungsscheinKundenSicht(BaseModel):
    """Reduzierte Kundensicht: kein status_intern, keine internen Notizen."""

    id: uuid.UUID
    ls_nummer: str
    auftrag_id: uuid.UUID
    leistung_id: Optional[uuid.UUID] = None
    scope_beschreibung: Optional[str] = None
    startdatum: Optional[date] = None
    kickoff_datum: Optional[datetime] = None
    workshop_datum: Optional[datetime] = None
    solltermin: Optional[date] = None
    status_kunde: str
    naechster_schritt: Optional[str] = None
    voraussetzungen: Optional[str] = None
    onboarding_ziele: Optional[str] = None
    onboarding_offene_punkte: Optional[str] = None
    aufgaben: list[AufgabeOut] = []
    workshops: list[WorkshopOut] = []

    model_config = {"from_attributes": True}


class LeistungsscheinInternSicht(LeistungsscheinKundenSicht):
    customer_id: uuid.UUID
    verantwortlicher_id: Optional[uuid.UUID] = None
    status_intern: Optional[str] = None
    onboarding_teilnehmer: Optional[list[Any]] = None
    lessons_learned: Optional[str] = None
    abschlussstatus: Optional[str] = None


class LeistungsscheinInternUpdate(BaseModel):
    scope_beschreibung: Optional[str] = None
    verantwortlicher_id: Optional[uuid.UUID] = None
    startdatum: Optional[date] = None
    kickoff_datum: Optional[datetime] = None
    workshop_datum: Optional[datetime] = None
    solltermin: Optional[date] = None
    status_kunde: Optional[str] = None
    status_intern: Optional[str] = None
    naechster_schritt: Optional[str] = None
    voraussetzungen: Optional[str] = None
    onboarding_ziele: Optional[str] = None
    onboarding_teilnehmer: Optional[list[Any]] = None
    onboarding_offene_punkte: Optional[str] = None
    lessons_learned: Optional[str] = None
    abschlussstatus: Optional[str] = None
