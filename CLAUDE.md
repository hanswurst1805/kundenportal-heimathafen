# CLAUDE.md – Kundenportal Heimathafen

Projektkontext für Claude Code. Details zum Aufbau stehen chronologisch in
[BUILD_LOG.md](BUILD_LOG.md), zum Deployment in [deploy/README.md](deploy/README.md).

## Was ist das

Kundenportal für IT-Systemhäuser/MSPs (Anfrage → Angebot → Beauftragung → AVV →
Auftrag → Leistungsschein mit Workshops/Aufgaben → Zufriedenheitsumfrage), mit
voller Status-Transparenz für den Kunden. Umgesetzt als MVP gemäß
`fachkonzept-kundenportal-signatur-workflow-v2.md` (liegt außerhalb des Repos).
Jeder Fachbereich hat einen vollständigen API-Satz; das Frontend ist reiner
API-Konsument.

## Tech-Stack

- **Backend**: FastAPI (async, Python 3.12), SQLAlchemy 2.0 (async, asyncpg),
  PostgreSQL 16, Alembic, Pydantic v2, JWT (python-jose) + bcrypt + TOTP-2FA (pyotp)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind v4 + React Router v7 +
  TanStack Query v5 + lucide-react (dunkles Theme: slate-950 / sky-600)
- **Signatur (inhouse)**: reportlab + pyhanko (PAdES) + pillow + cryptography;
  Frontend signature_pad
- **Betrieb**: Podman (Entwicklung: `podman-compose.yml`; Produktion:
  `podman-compose.prod.yml` + Caddy; VPS ohne compose: `deploy/kundenportal.sh`)

## Wichtige Befehle (Entwicklung, alles in Containern)

```bash
# Stack starten (DB, API, Frontend)
podman compose -f podman-compose.yml up -d db api frontend
#   (docker compose funktioniert ebenso, falls Podman über Docker-CLI läuft)

# Migrationen
podman compose -f podman-compose.yml exec api alembic upgrade head
podman compose -f podman-compose.yml exec api sh -c "alembic downgrade base && alembic upgrade head"  # DB reset

# Demo-Daten (idempotent)
podman compose -f podman-compose.yml exec api python scripts/seed_demo_data.py

# Backend-Tests (Integrationstests gegen laufende API; frische DB nötig)
podman compose -f podman-compose.yml exec api sh -c "pip install -q '.[dev]' pyotp && python -m pytest tests/ -q"

# Frontend prüfen (Pflicht vor Commit)
podman compose -f podman-compose.yml exec frontend sh -c "npx tsc -b && npx eslint ."
```

- Frontend: http://localhost:5173 · API/OpenAPI: http://localhost:8000/docs
- `.env` (aus `.env.example`) ist **nicht** in Git; `data/` (signierte PDFs +
  Siegelzertifikat) ebenfalls nicht.

## Struktur

```
src/
  main.py            FastAPI-App + lifespan (Bootstrap-Admin)
  core/              config, database (async), auth (JWT/2FA/Rollen), status_codes, status_engine, bootstrap
  models/            ein Modul je Fachobjekt (customer, user, leistung, anfrage, angebot,
                     bestellung, signatur, avv, auftrag, leistungsschein, dokument, ereignis, umfrage, status)
  schemas/           Pydantic-Schemas (teils Kunden- vs. interne Sicht)
  api/
    auth.py          /auth/* (Login, 2FA-Setup/Verify, Passwort)
    customer/        /api/v1/portal/*  (require_customer, mandantengefiltert)
    internal/        /api/v1/intern/*  (require_role("user","admin"); admin-only: statusregeln, users, avv-vorlagen)
  adapters/          signature|avv|target_system|notification + registry (signature: nur "inhouse"; übrige: "stub")
  automation/        events (In-Process Event-Bus), rules (StatusRegel), handlers (9 Trigger), dedup
  services/          numbering, origin, auftrag_service, signatur_resolve, pdf_signing
frontend/src/        api/client.ts, components/, pages/{customer,internal}, lib/
scripts/             seed_demo_data.py, entrypoint.sh (Prod: Migrationen + uvicorn)
deploy/              kundenportal.sh (reines Podman), *.env.example, README.md
tests/               conftest.py, test_integration.py, test_signatur_inhouse.py
```

## Fachliche Kernkonzepte

- **Rollen**: `admin` (alles inkl. Statusregeln/Benutzer/Vorlagen), `user`
  (operative interne Bearbeitung), `kunde` (Portal, `customer_id`-gebunden).
  **2FA (TOTP)** für alle möglich und standardmäßig **optional**. Per Setting
  `REQUIRE_2FA=true` wird sie für `admin`/`user` zur Pflicht (Backend erzwingt dann
  die Einrichtung vor Zugriff auf geschützte Endpunkte). Setup zeigt QR-Code.
- **Mandantentrennung**: jede Kunden-Query über `ctx.customer_id`;
  `require_customer_scope` wirft 404 bei Fremdzugriff.
- **Status**: 15 kundensichtbare Hauptstatus + interne Zwischenschritte in
  `src/core/status_codes.py` (Frontend gespiegelt in `frontend/src/lib/statuscodes.ts`).
  Übergänge laufen über den Event-Bus (`automation/`); `StatusRegel` (per Migration
  0002 geseedet) steuert Zielstatus + Benachrichtigung.
- **Adapter** (austauschbar via `settings.*_provider`):
  - `signature`: nur `inhouse` (Unterschrift zeichnen → PDF mit Audit-Trail,
    kryptografisch versiegelt = FES; Siegel-Zertifikat selbstsigniert auto-erzeugt
    unter `data/signing/`). Der frühere `stub`-Klick-Signatur-Provider wurde entfernt.
  - `avv`, `target_system`, `notification`: jeweils `stub`

## Konventionen

- Nach jedem abgeschlossenen Schritt: kurzer Eintrag in `BUILD_LOG.md`, dann
  `git commit` + `git push` auf `origin/main`.
- Vor dem Commit: Frontend `tsc -b` + `eslint` fehlerfrei; bei Backend-Änderungen
  die Test-Suite laufen lassen.
- Code im Stil der Umgebung (Sprache: deutschsprachige Labels/Kommentare,
  englische Bezeichner gemischt wie im Bestand).
- Commit-/PR-Sprache deutsch, fachlich knapp.

## GitHub

Privates Repo `git@github.com:hanswurst1805/kundenportal-heimathafen.git`
(Branch `main`). Vor dem Arbeiten `git pull`.
