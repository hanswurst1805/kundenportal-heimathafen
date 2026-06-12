"""Sammelpunkt fuer alle SQLAlchemy-Modelle - wird von Alembic importiert,
damit alle Tabellen in Base.metadata registriert sind."""

from src.models.base import Base
from src.models.customer import Customer
from src.models.user import User
from src.models.leistung import Leistung
from src.models.anfrage import Anfrage
from src.models.angebot import Angebot, AngebotPosition
from src.models.bestellung import Bestellung
from src.models.signatur import Signaturvorgang
from src.models.avv import AVV, AVVVorlage
from src.models.auftrag import Auftrag, Auftragsbestaetigung
from src.models.leistungsschein import Leistungsschein, Workshop, Aufgabe
from src.models.dokument import Dokument
from src.models.ereignis import Ereignisprotokoll
from src.models.umfrage import Umfrage
from src.models.status import StatusRegel

__all__ = [
    "Base",
    "Customer",
    "User",
    "Leistung",
    "Anfrage",
    "Angebot",
    "AngebotPosition",
    "Bestellung",
    "Signaturvorgang",
    "AVV",
    "AVVVorlage",
    "Auftrag",
    "Auftragsbestaetigung",
    "Leistungsschein",
    "Workshop",
    "Aufgabe",
    "Dokument",
    "Ereignisprotokoll",
    "Umfrage",
    "StatusRegel",
]
