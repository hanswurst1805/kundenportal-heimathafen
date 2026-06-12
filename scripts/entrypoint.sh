#!/bin/sh
# Produktions-Entrypoint des API-Containers:
# fuehrt vor dem Start die ausstehenden DB-Migrationen aus und startet
# anschliessend den uvicorn-Server (ohne --reload).
set -e

echo "[entrypoint] Warte auf Datenbank und fuehre Migrationen aus..."
alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
    echo "[entrypoint] SEED_DEMO_DATA=true -> lege Demo-Daten an (idempotent)..."
    python scripts/seed_demo_data.py || echo "[entrypoint] Seed uebersprungen/fehlgeschlagen (ggf. bereits vorhanden)."
fi

echo "[entrypoint] Starte API-Server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
