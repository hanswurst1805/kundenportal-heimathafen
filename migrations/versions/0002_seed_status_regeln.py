"""Seed der StatusRegel-Konfiguration (9 Trigger aus dem Fachkonzept).

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-12
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


status_regeln_table = table(
    "status_regeln",
    column("id", postgresql.UUID(as_uuid=True)),
    column("ereignis_typ", sa.String),
    column("ziel_status_kunde", sa.String),
    column("benachrichtigung", sa.String),
    column("aktiv", sa.Boolean),
    column("beschreibung", sa.Text),
)

SEED_ROWS = [
    ("signature_completed", "beauftragt", "ja", "Signatur abgeschlossen -> Beauftragung wirksam (sofern kein AVV erforderlich)."),
    ("avv_required", "avv_ausstehend", "ja", "AVV-Unterzeichnung erforderlich vor Beauftragung."),
    ("avv_completed", "beauftragt", "ja", "AVV unterzeichnet -> Beauftragung wirksam."),
    ("kickoff_scheduled", "kickoff_gestartet", "optional", "Kick-Off-Termin vereinbart."),
    ("onboarding_workshop_scheduled", "onboarding_workshop", "optional", "Onboarding-Workshop-Termin vereinbart."),
    ("onboarding_workshop_finished", "in_bearbeitung", "optional", "Onboarding-Workshop durchgefuehrt, Protokoll freigegeben."),
    ("customer_input_required", "warten_auf_kunde", "ja", "Rueckmeldung des Kunden erforderlich (immer benachrichtigen)."),
    ("delivery_completed", "fertiggestellt", "ja", "Leistung fertiggestellt, Umfrage wird angelegt."),
    ("survey_sent", "kundenzufriedenheitsabfrage", "ja", "Zufriedenheitsumfrage versendet."),
]


def upgrade() -> None:
    op.bulk_insert(
        status_regeln_table,
        [
            {
                "id": uuid.uuid4(),
                "ereignis_typ": ereignis_typ,
                "ziel_status_kunde": ziel_status,
                "benachrichtigung": benachrichtigung,
                "aktiv": True,
                "beschreibung": beschreibung,
            }
            for ereignis_typ, ziel_status, benachrichtigung, beschreibung in SEED_ROWS
        ],
    )


def downgrade() -> None:
    ereignis_typen = [row[0] for row in SEED_ROWS]
    op.execute(
        status_regeln_table.delete().where(status_regeln_table.c.ereignis_typ.in_(ereignis_typen))
    )
