"""Sammelpunkt fuer alle SQLAlchemy-Modelle - wird von Alembic importiert,
damit alle Tabellen in Base.metadata registriert sind."""

from src.models.base import Base  # noqa: F401

__all__ = ["Base"]
