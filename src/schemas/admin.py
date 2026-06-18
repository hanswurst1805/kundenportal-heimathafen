from __future__ import annotations

from pydantic import BaseModel


class SystemResetRequest(BaseModel):
    # Schutz vor versehentlichem Aufruf: muss exakt "RESET" sein.
    bestaetigung: str


class SystemResetResult(BaseModel):
    geleerte_tabellen: list[str]
    geloeschte_dateien: int
