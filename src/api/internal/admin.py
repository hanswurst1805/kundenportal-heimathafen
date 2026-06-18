"""Administrative Wartungsfunktionen (admin-only). Enthaelt den System-Reset,
der alle Geschaeftsdaten und abgelegten Dateien loescht."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.bootstrap import bootstrap_admin
from src.core.database import get_session
from src.models.base import Base
from src.schemas.admin import SystemResetRequest, SystemResetResult
from src.services.pdf_signing import documents_dir

logger = logging.getLogger(__name__)

# Tabellen, die beim Reset erhalten bleiben (per Migration geseedete
# Automatisierungs-Konfiguration – sonst stuende die Status-Engine ohne Regeln da).
PRESERVE_TABLES = {"status_regeln"}
BESTAETIGUNG = "RESET"

router = APIRouter(
    prefix="/admin", tags=["intern-admin"], dependencies=[Depends(require_role("admin"))]
)


def _clear_directory(path: Path) -> int:
    """Loescht den gesamten Inhalt eines Verzeichnisses (Ordner bleibt bestehen).
    Gibt die Anzahl entfernter Dateien zurueck."""
    if not path.exists():
        return 0
    anzahl = sum(1 for p in path.rglob("*") if p.is_file())
    for eintrag in path.iterdir():
        if eintrag.is_dir():
            shutil.rmtree(eintrag, ignore_errors=True)
        else:
            eintrag.unlink(missing_ok=True)
    return anzahl


@router.post("/reset", response_model=SystemResetResult)
async def reset_system(
    data: SystemResetRequest, session: AsyncSession = Depends(get_session)
):
    """Setzt das System zurueck: leert alle Geschaeftsdaten (Tabellen ausser der
    Automatisierungs-Konfiguration), loescht abgelegte Dateien (signierte PDFs +
    Siegel-Zertifikat) und legt den initialen Admin neu an."""
    if data.bestaetigung != BESTAETIGUNG:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bestätigung erforderlich: bitte exakt '{BESTAETIGUNG}' senden.",
        )

    # 1) Dateien loeschen (Dokumentenablage + Siegel-Zertifikat)
    docs = documents_dir()
    signing = docs.parent / "signing"
    geloeschte_dateien = _clear_directory(docs) + _clear_directory(signing)

    # 2) Tabellen leeren – FK-sicher in umgekehrter Abhaengigkeitsreihenfolge
    geleerte_tabellen: list[str] = []
    for table in reversed(Base.metadata.sorted_tables):
        if table.name in PRESERVE_TABLES:
            continue
        await session.execute(delete(table))
        geleerte_tabellen.append(table.name)
    await session.commit()

    # 3) Initialen Admin neu anlegen (alle Benutzer wurden geloescht)
    await bootstrap_admin()

    logger.warning(
        "SYSTEM-RESET durch Admin: %d Tabellen geleert, %d Dateien geloescht.",
        len(geleerte_tabellen),
        geloeschte_dateien,
    )
    return SystemResetResult(
        geleerte_tabellen=sorted(geleerte_tabellen), geloeschte_dateien=geloeschte_dateien
    )
