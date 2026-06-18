"""Angebotsposition: optionale Verknuepfung mit einer Katalog-Leistung.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "angebot_positionen",
        sa.Column("leistung_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_angebot_positionen_leistung",
        "angebot_positionen",
        "leistungen",
        ["leistung_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_angebot_positionen_leistung", "angebot_positionen", type_="foreignkey")
    op.drop_column("angebot_positionen", "leistung_id")
