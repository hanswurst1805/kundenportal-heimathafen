"""Demo-/Seed-Daten fuer das Kundenportal Heimathafen (Schritt 10).

Legt einen reproduzierbaren Demo-Datenbestand an, der den kompletten
Fachprozess abbildet:

- StatusRegel-Konfiguration fuer alle 9 Automatisierungs-Trigger
- 1 aktive AVV-Vorlage
- 5 Katalogleistungen (mind. eine mit AVV-Pflicht)
- 2 Demo-Kunden, je ein Kunden-User; ein interner `user` und ein `admin`
- eine offene Anfrage im Status `in_pruefung`
- ein vollstaendig durchlaufenes Beispiel: Bestellung -> Signatur -> AVV ->
  Auftrag/Leistungsschein mit Kick-Off- und Onboarding-Workshop (Protokoll
  freigegeben) sowie mehreren Aufgaben (Status `in_bearbeitung`)

Treibt die Workflow-Automatisierung ueber denselben Event-Bus an, den auch die
API verwendet (`src.automation.events.publish`), damit die erzeugten Daten zu
den realen Statusuebergaengen passen.

Idempotent: bricht ab, wenn der Demo-Bestand (Kunde `K-1001`) bereits existiert.

Aufruf (gegen die laufende Podman-DB):
    python scripts/seed_demo_data.py
oder im API-Container:
    docker compose -f podman-compose.yml exec api python scripts/seed_demo_data.py
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from src.adapters.registry import get_signature_provider
from src.automation.events import publish
from src.core.auth import hash_password
from src.core.database import get_async_session_factory
from src.core.status_codes import (
    EVENT_AVV_COMPLETED,
    EVENT_AVV_REQUIRED,
    EVENT_CUSTOMER_INPUT_REQUIRED,
    EVENT_DELIVERY_COMPLETED,
    EVENT_KICKOFF_SCHEDULED,
    EVENT_ONBOARDING_WORKSHOP_FINISHED,
    EVENT_ONBOARDING_WORKSHOP_SCHEDULED,
    EVENT_SIGNATURE_COMPLETED,
    EVENT_SURVEY_SENT,
    NOTIFY_JA,
    NOTIFY_NEIN,
    NOTIFY_OPTIONAL,
)
from src.models.anfrage import Anfrage
from src.models.avv import AVV, AVV_AUSSTEHEND, AVVVorlage
from src.models.bestellung import Bestellung
from src.models.customer import Customer
from src.models.ereignis import AKTEUR_USER
from src.models.leistung import Leistung
from src.models.leistungsschein import (
    AUFGABE_ERLEDIGT,
    AUFGABE_IN_BEARBEITUNG,
    AUFGABE_OFFEN,
    WORKSHOP_GEPLANT,
    WORKSHOP_PROTOKOLL_FREIGEGEBEN,
    WORKSHOP_TYP_KICKOFF,
    WORKSHOP_TYP_ONBOARDING,
    Aufgabe,
    Leistungsschein,
    Workshop,
)
from src.models.signatur import BEZUG_BESTELLUNG, SIGNATUR_SIGNIERT
from src.models.status import StatusRegel
from src.models.user import ROLE_ADMIN, ROLE_KUNDE, ROLE_USER, User
from src.services.numbering import next_number

# Demo-Passwoerter (nur fuer lokale Demo/Entwicklung!)
PW_ADMIN = "admin-demo-123"
PW_USER = "user-demo-123"
PW_KUNDE = "kunde-demo-123"


# Trigger -> (kundensichtbarer Zielstatus, Benachrichtigungsstufe, Beschreibung)
STATUS_REGELN = [
    (EVENT_SIGNATURE_COMPLETED, "beauftragt", NOTIFY_JA, "Signatur abgeschlossen"),
    (EVENT_AVV_REQUIRED, "avv_ausstehend", NOTIFY_JA, "AVV erforderlich – Kunde muss zustimmen"),
    (EVENT_AVV_COMPLETED, "beauftragt", NOTIFY_JA, "AVV abgeschlossen"),
    (EVENT_KICKOFF_SCHEDULED, "kickoff_gestartet", NOTIFY_OPTIONAL, "Kick-Off geplant"),
    (EVENT_ONBOARDING_WORKSHOP_SCHEDULED, "onboarding_workshop", NOTIFY_OPTIONAL, "Onboarding-Workshop geplant"),
    (EVENT_ONBOARDING_WORKSHOP_FINISHED, "in_bearbeitung", NOTIFY_OPTIONAL, "Workshop-Protokoll freigegeben"),
    (EVENT_CUSTOMER_INPUT_REQUIRED, "warten_auf_kunde", NOTIFY_JA, "Rueckfrage an den Kunden"),
    (EVENT_DELIVERY_COMPLETED, "fertiggestellt", NOTIFY_JA, "Leistung fertiggestellt"),
    (EVENT_SURVEY_SENT, "kundenzufriedenheitsabfrage", NOTIFY_NEIN, "Zufriedenheitsumfrage versendet"),
]


async def _ensure_admin(session) -> User:
    admin = (await session.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
    if admin:
        return admin
    admin = User(
        username="admin",
        password_hash=hash_password(PW_ADMIN),
        role=ROLE_ADMIN,
        display_name="Administrator (Demo)",
        totp_required=True,
    )
    session.add(admin)
    await session.flush()
    return admin


async def seed() -> None:
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        existing = (
            await session.execute(select(Customer).where(Customer.kundennummer == "K-1001"))
        ).scalar_one_or_none()
        if existing:
            print("Demo-Daten bereits vorhanden (Kunde K-1001). Abbruch.")
            return

        # 1. StatusRegeln
        await _seed_status_regeln(session)

        # 2. AVV-Vorlage
        vorlage = AVVVorlage(
            name="Standard-AVV (Art. 28 DSGVO)",
            version="1.0",
            inhalt="Auftragsverarbeitungsvertrag gemaess Art. 28 DSGVO – Demo-Inhalt.",
            is_active=True,
        )
        session.add(vorlage)

        # 3. Katalogleistungen
        leistungen = [
            Leistung(
                leistungs_id="MS-100",
                name="Managed Workplace",
                beschreibung="Vollstaendig verwalteter Arbeitsplatz inkl. Patch- und Endpoint-Management.",
                kategorie="Managed Services",
                preis=Decimal("49.90"),
                preiseinheit="pro Monat",
                avv_erforderlich=True,
            ),
            Leistung(
                leistungs_id="MS-200",
                name="Managed Backup",
                beschreibung="Tägliche Sicherung mit Monitoring und Wiederherstellungstest.",
                kategorie="Managed Services",
                preis=Decimal("29.00"),
                preiseinheit="pro Monat",
                avv_erforderlich=True,
            ),
            Leistung(
                leistungs_id="PR-010",
                name="IT-Sicherheitsaudit",
                beschreibung="Einmalige Bestandsaufnahme und Bewertung der IT-Sicherheit.",
                kategorie="Projekte",
                preis=Decimal("1850.00"),
                preiseinheit="einmalig",
                avv_erforderlich=False,
            ),
            Leistung(
                leistungs_id="PR-020",
                name="Microsoft 365 Einführung",
                beschreibung="Migration und Onboarding-Workshop für Microsoft 365.",
                kategorie="Projekte",
                preis=Decimal("3200.00"),
                preiseinheit="einmalig",
                avv_erforderlich=False,
            ),
            Leistung(
                leistungs_id="SUP-001",
                name="Support-Kontingent 10h",
                beschreibung="Flexibel abrufbares Support-Kontingent von 10 Stunden.",
                kategorie="Support",
                preis=Decimal("950.00"),
                preiseinheit="einmalig",
                avv_erforderlich=False,
            ),
        ]
        session.add_all(leistungen)
        await session.flush()
        leistung_mw = leistungen[0]  # Managed Workplace (AVV-pflichtig)

        # 4. Benutzer (admin / interner user)
        admin = await _ensure_admin(session)  # noqa: F841 – Referenz fuer Lesbarkeit
        intern_user = User(
            username="mitarbeiter",
            password_hash=hash_password(PW_USER),
            role=ROLE_USER,
            display_name="Maria Mustermann (Innendienst)",
            totp_required=True,
        )
        session.add(intern_user)
        await session.flush()

        # 5. Kunden + Kunden-User
        kunde1 = Customer(
            kundennummer="K-1001",
            name="Nordlicht Logistik GmbH",
            short_name="Nordlicht",
            contact_name="Jens Petersen",
            contact_email="demo+nordlicht@heihaf.kiste.org",
            contact_phone="040 123456",
            address="Hafenstraße 1, 20457 Hamburg",
        )
        kunde2 = Customer(
            kundennummer="K-1002",
            name="Alpenblick Steuerberatung",
            short_name="Alpenblick",
            contact_name="Sabine Huber",
            contact_email="demo+alpenblick@heihaf.kiste.org",
            contact_phone="089 987654",
            address="Bergweg 7, 80331 München",
        )
        session.add_all([kunde1, kunde2])
        await session.flush()

        session.add_all(
            [
                User(
                    username="kunde1",
                    password_hash=hash_password(PW_KUNDE),
                    role=ROLE_KUNDE,
                    customer_id=kunde1.id,
                    display_name="Jens Petersen",
                ),
                User(
                    username="kunde2",
                    password_hash=hash_password(PW_KUNDE),
                    role=ROLE_KUNDE,
                    customer_id=kunde2.id,
                    display_name="Sabine Huber",
                ),
            ]
        )

        # 6. Offene Anfrage (in_pruefung) fuer Kunde 2
        anfrage = Anfrage(
            anfrage_nr=await next_number(session, Anfrage, "ANF"),
            customer_id=kunde2.id,
            thema="Migration der Kanzleisoftware in die Cloud",
            beschreibung="Wir möchten unsere DATEV-Umgebung in eine gehostete Lösung überführen.",
            fachbereich="Cloud & Infrastruktur",
            prioritaet="hoch",
            status_kunde="in_pruefung",
            status_intern="anfrage_klassifiziert",
        )
        session.add(anfrage)
        await session.flush()

        # 7. Vollständiger Durchlauf für Kunde 1 (Managed Workplace, AVV-pflichtig)
        await _seed_durchlauf(session, kunde1, leistung_mw, intern_user)

        await session.commit()

    print("Demo-Daten erfolgreich angelegt.")
    print("  Logins (Passwörter nur für die lokale Demo):")
    print(f"    admin       / {PW_ADMIN}   (2FA-Einrichtung beim ersten Login erforderlich)")
    print(f"    mitarbeiter / {PW_USER}    (Rolle user, 2FA-Pflicht)")
    print(f"    kunde1      / {PW_KUNDE}   (Nordlicht Logistik GmbH)")
    print(f"    kunde2      / {PW_KUNDE}   (Alpenblick Steuerberatung)")


async def _seed_status_regeln(session) -> None:
    for ereignis_typ, ziel, notify, beschreibung in STATUS_REGELN:
        vorhanden = (
            await session.execute(select(StatusRegel).where(StatusRegel.ereignis_typ == ereignis_typ))
        ).scalar_one_or_none()
        if vorhanden:
            continue
        session.add(
            StatusRegel(
                ereignis_typ=ereignis_typ,
                ziel_status_kunde=ziel,
                benachrichtigung=notify,
                aktiv=True,
                beschreibung=beschreibung,
            )
        )
    await session.flush()


async def _seed_durchlauf(session, kunde: Customer, leistung: Leistung, intern_user: User) -> None:
    # Bestellung anlegen + Signaturvorgang erzeugen (wie der Portal-Endpoint)
    bestellung = Bestellung(
        bestell_nr=await next_number(session, Bestellung, "BES"),
        customer_id=kunde.id,
        leistung_id=leistung.id,
    )
    session.add(bestellung)
    await session.flush()

    vorgang = await get_signature_provider().create_envelope(
        session, BEZUG_BESTELLUNG, bestellung.id, f"Beauftragung {leistung.name}"
    )

    # Kunde signiert -> signature_completed -> avv_required (AVV ausstehend)
    vorgang.status = SIGNATUR_SIGNIERT
    vorgang.signierzeit = datetime.now(timezone.utc)
    await publish(
        session,
        EVENT_SIGNATURE_COMPLETED,
        customer_id=kunde.id,
        bezugstyp=vorgang.bezugstyp,
        bezugs_id=vorgang.bezugs_id,
        akteur_typ=AKTEUR_USER,
    )

    # Kunde nimmt AVV an -> avv_completed -> Auftrag + Leistungsschein (beauftragt)
    avv = (
        await session.execute(
            select(AVV).where(AVV.bezugs_id == bestellung.id, AVV.status == AVV_AUSSTEHEND)
        )
    ).scalar_one_or_none()
    if avv is not None:
        await publish(
            session,
            EVENT_AVV_COMPLETED,
            customer_id=kunde.id,
            bezugstyp="avv",
            bezugs_id=avv.id,
            akteur_typ=AKTEUR_USER,
        )

    # Frisch angelegten Leistungsschein ermitteln
    ls = (
        await session.execute(
            select(Leistungsschein)
            .where(Leistungsschein.customer_id == kunde.id)
            .order_by(Leistungsschein.created_at.desc())
        )
    ).scalars().first()
    if ls is None:
        return

    ls.verantwortlicher_id = intern_user.id
    ls.startdatum = date.today()
    ls.solltermin = date.today() + timedelta(days=30)
    ls.naechster_schritt = "Onboarding-Aufgaben abarbeiten"
    ls.onboarding_ziele = "Reibungsloser Rollout des Managed Workplace für alle 25 Mitarbeitenden."

    # Kick-Off-Workshop -> kickoff_gestartet
    kickoff = Workshop(
        leistungsschein_id=ls.id,
        typ=WORKSHOP_TYP_KICKOFF,
        termin=datetime.now(timezone.utc) + timedelta(days=2),
        status=WORKSHOP_GEPLANT,
    )
    session.add(kickoff)
    await session.flush()
    await publish(
        session,
        EVENT_KICKOFF_SCHEDULED,
        customer_id=kunde.id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        akteur_id=intern_user.id,
        akteur_typ=AKTEUR_USER,
        payload={"workshop_id": str(kickoff.id)},
    )

    # Onboarding-Workshop -> onboarding_workshop
    onboarding = Workshop(
        leistungsschein_id=ls.id,
        typ=WORKSHOP_TYP_ONBOARDING,
        termin=datetime.now(timezone.utc) + timedelta(days=7),
        status=WORKSHOP_GEPLANT,
    )
    session.add(onboarding)
    await session.flush()
    await publish(
        session,
        EVENT_ONBOARDING_WORKSHOP_SCHEDULED,
        customer_id=kunde.id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        akteur_id=intern_user.id,
        akteur_typ=AKTEUR_USER,
        payload={"workshop_id": str(onboarding.id)},
    )

    # Protokoll freigeben -> onboarding_workshop_finished -> in_bearbeitung
    onboarding.protokoll = "Workshop durchgeführt, Zugänge und Zeitplan abgestimmt."
    onboarding.status = WORKSHOP_PROTOKOLL_FREIGEGEBEN
    await publish(
        session,
        EVENT_ONBOARDING_WORKSHOP_FINISHED,
        customer_id=kunde.id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        akteur_id=intern_user.id,
        akteur_typ=AKTEUR_USER,
        payload={"workshop_id": str(onboarding.id)},
    )

    # Aufgabenpaket
    session.add_all(
        [
            Aufgabe(
                leistungsschein_id=ls.id,
                titel="Geräte inventarisieren",
                beschreibung="Bestandsaufnahme aller 25 Endgeräte.",
                zustaendigkeit_id=intern_user.id,
                faelligkeit=date.today() + timedelta(days=5),
                status=AUFGABE_ERLEDIGT,
                sort_order=0,
            ),
            Aufgabe(
                leistungsschein_id=ls.id,
                titel="Patch-Management ausrollen",
                beschreibung="Agenten installieren und Richtlinien zuweisen.",
                zustaendigkeit_id=intern_user.id,
                faelligkeit=date.today() + timedelta(days=12),
                status=AUFGABE_IN_BEARBEITUNG,
                sort_order=1,
            ),
            Aufgabe(
                leistungsschein_id=ls.id,
                titel="Abschlussdokumentation erstellen",
                zustaendigkeit_id=intern_user.id,
                faelligkeit=date.today() + timedelta(days=25),
                status=AUFGABE_OFFEN,
                sort_order=2,
            ),
        ]
    )


if __name__ == "__main__":
    asyncio.run(seed())
