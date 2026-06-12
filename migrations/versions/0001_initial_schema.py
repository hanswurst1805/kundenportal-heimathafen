"""Initiales Datenmodell: alle 16 Fachobjekte des Kundenportals.

Revision ID: 0001
Revises:
Create Date: 2026-06-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kundennummer", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(64), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(64), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_customers_kundennummer", "customers", ["kundennummer"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="kunde"),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("totp_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("backup_codes", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "leistungen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("leistungs_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("kategorie", sa.String(128), nullable=True),
        sa.Column("preis", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("preiseinheit", sa.String(32), nullable=False, server_default="einmalig"),
        sa.Column("avv_erforderlich", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ist_bestellbar", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leistungen_leistungs_id", "leistungen", ["leistungs_id"], unique=True)

    op.create_table(
        "anfragen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anfrage_nr", sa.String(32), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("ersteller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("thema", sa.String(255), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("fachbereich", sa.String(128), nullable=True),
        sa.Column("prioritaet", sa.String(16), nullable=False, server_default="mittel"),
        sa.Column("status_kunde", sa.String(64), nullable=False, server_default="anfrage_eingegangen"),
        sa.Column("status_intern", sa.String(64), nullable=True),
        sa.Column("angebot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_anfragen_anfrage_nr", "anfragen", ["anfrage_nr"], unique=True)

    op.create_table(
        "angebote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("angebotsnummer", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("anfrage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anfragen.id"), nullable=True),
        sa.Column("leistung_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leistungen.id"), nullable=True),
        sa.Column("titel", sa.String(255), nullable=False),
        sa.Column("gueltig_bis", sa.Date(), nullable=True),
        sa.Column("gesamtpreis", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="entwurf"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_angebote_angebotsnummer", "angebote", ["angebotsnummer"], unique=True)

    op.create_table(
        "angebot_positionen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("angebot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("angebote.id"), nullable=False),
        sa.Column("bezeichnung", sa.String(255), nullable=False),
        sa.Column("menge", sa.Numeric(10, 2), nullable=False, server_default="1"),
        sa.Column("einzelpreis", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("gesamtpreis", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "bestellungen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bestell_nr", sa.String(32), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("leistung_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leistungen.id"), nullable=False),
        sa.Column("besteller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("bestelldatum", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="warten_auf_signatur"),
        sa.Column("angebot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("angebote.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bestellungen_bestell_nr", "bestellungen", ["bestell_nr"], unique=True)

    op.create_table(
        "signaturvorgaenge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bezugstyp", sa.String(32), nullable=False),
        sa.Column("bezugs_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anbieter", sa.String(32), nullable=False, server_default="stub"),
        sa.Column("anbieter_referenz", sa.String(255), nullable=True),
        sa.Column("token", sa.String(64), nullable=True),
        sa.Column("signatur_link", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="erstellt"),
        sa.Column("versandzeit", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signierzeit", sa.DateTime(timezone=True), nullable=True),
        sa.Column("erinnerung_gesendet_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_signaturvorgaenge_bezugstyp", "signaturvorgaenge", ["bezugstyp"])
    op.create_index("ix_signaturvorgaenge_bezugs_id", "signaturvorgaenge", ["bezugs_id"])
    op.create_index("ix_signaturvorgaenge_token", "signaturvorgaenge", ["token"], unique=True)

    op.create_table(
        "avv_vorlagen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0"),
        sa.Column("inhalt", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "avv",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("bezugstyp", sa.String(32), nullable=False),
        sa.Column("bezugs_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pflicht", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vorlage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("avv_vorlagen.id"), nullable=True),
        sa.Column("version", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="nicht_erforderlich"),
        sa.Column(
            "signaturvorgang_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("signaturvorgaenge.id"),
            nullable=True,
        ),
        sa.Column("abschlussdatum", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_avv_bezugs_id", "avv", ["bezugs_id"])

    op.create_table(
        "auftraege",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auftragsnummer", sa.String(32), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("ursprung_typ", sa.String(32), nullable=False),
        sa.Column("ursprung_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="entwurf"),
        sa.Column("freigabedatum", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auftraege_auftragsnummer", "auftraege", ["auftragsnummer"], unique=True)

    op.create_table(
        "leistungsscheine",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ls_nummer", sa.String(32), nullable=False),
        sa.Column("auftrag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auftraege.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("leistung_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leistungen.id"), nullable=True),
        sa.Column("scope_beschreibung", sa.Text(), nullable=True),
        sa.Column("verantwortlicher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("startdatum", sa.Date(), nullable=True),
        sa.Column("kickoff_datum", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workshop_datum", sa.DateTime(timezone=True), nullable=True),
        sa.Column("solltermin", sa.Date(), nullable=True),
        sa.Column("status_kunde", sa.String(64), nullable=False, server_default="beauftragt"),
        sa.Column("status_intern", sa.String(64), nullable=True),
        sa.Column("naechster_schritt", sa.Text(), nullable=True),
        sa.Column("voraussetzungen", sa.Text(), nullable=True),
        sa.Column("onboarding_ziele", sa.Text(), nullable=True),
        sa.Column("onboarding_teilnehmer", postgresql.JSONB(), nullable=True),
        sa.Column("onboarding_offene_punkte", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("abschlussstatus", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leistungsscheine_ls_nummer", "leistungsscheine", ["ls_nummer"], unique=True)
    op.create_unique_constraint("uq_leistungsscheine_auftrag_id", "leistungsscheine", ["auftrag_id"])

    op.create_table(
        "dokumente",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("typ", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sichtbarkeit", sa.String(16), nullable=False, server_default="intern"),
        sa.Column("dateiname", sa.String(255), nullable=False),
        sa.Column("ablageort", sa.String(512), nullable=False),
        sa.Column("bezugstyp", sa.String(32), nullable=True),
        sa.Column("bezugs_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "leistungsschein_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leistungsscheine.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "auftragsbestaetigungen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auftrag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auftraege.id"), nullable=False),
        sa.Column("dokument_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dokumente.id"), nullable=True),
        sa.Column("bereitgestellt_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kenntnisnahme_am", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_auftragsbestaetigungen_auftrag_id", "auftragsbestaetigungen", ["auftrag_id"]
    )

    op.create_table(
        "workshops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "leistungsschein_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leistungsscheine.id"),
            nullable=False,
        ),
        sa.Column("typ", sa.String(32), nullable=False),
        sa.Column("termin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("teilnehmer", postgresql.JSONB(), nullable=True),
        sa.Column("protokoll", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="geplant"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "aufgaben",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "leistungsschein_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leistungsscheine.id"),
            nullable=False,
        ),
        sa.Column("titel", sa.String(255), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("zustaendigkeit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("faelligkeit", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="offen"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ereignisprotokoll",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("zeit", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("akteur_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("akteur_typ", sa.String(16), nullable=False, server_default="system"),
        sa.Column("ereignis_typ", sa.String(64), nullable=False),
        sa.Column("bezugstyp", sa.String(32), nullable=True),
        sa.Column("bezugs_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vorher_status", sa.String(64), nullable=True),
        sa.Column("nachher_status", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("verarbeitet", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_ereignisprotokoll_zeit", "ereignisprotokoll", ["zeit"])
    op.create_index("ix_ereignisprotokoll_ereignis_typ", "ereignisprotokoll", ["ereignis_typ"])
    op.create_index("ix_ereignisprotokoll_bezugs_id", "ereignisprotokoll", ["bezugs_id"])

    op.create_table(
        "umfragen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "leistungsschein_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leistungsscheine.id"),
            nullable=False,
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("versandzeit", sa.DateTime(timezone=True), nullable=True),
        sa.Column("erinnert_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="geplant"),
        sa.Column("bewertung", sa.Integer(), nullable=True),
        sa.Column("kommentar", sa.Text(), nullable=True),
        sa.Column("beantwortet_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "status_regeln",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ereignis_typ", sa.String(64), nullable=False),
        sa.Column("ziel_status_kunde", sa.String(64), nullable=False),
        sa.Column("benachrichtigung", sa.String(16), nullable=False, server_default="optional"),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_status_regeln_ereignis_typ", "status_regeln", ["ereignis_typ"], unique=True)


def downgrade() -> None:
    op.drop_table("status_regeln")
    op.drop_table("umfragen")
    op.drop_table("ereignisprotokoll")
    op.drop_table("aufgaben")
    op.drop_table("workshops")
    op.drop_table("auftragsbestaetigungen")
    op.drop_table("dokumente")
    op.drop_table("leistungsscheine")
    op.drop_table("auftraege")
    op.drop_table("avv")
    op.drop_table("avv_vorlagen")
    op.drop_table("signaturvorgaenge")
    op.drop_table("bestellungen")
    op.drop_table("angebot_positionen")
    op.drop_table("angebote")
    op.drop_table("anfragen")
    op.drop_table("leistungen")
    op.drop_table("users")
    op.drop_table("customers")
