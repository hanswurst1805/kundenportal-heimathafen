# Build Log – Kundenportal Heimathafen

Fortlaufende Dokumentation der Implementierungsschritte (siehe Plan unter `fachkonzept-kundenportal-signatur-workflow-v2.md` im übergeordneten Ordner).

## Schritt 1: Backend-Grundgerüst

- Projektstruktur angelegt (`src/{core,models,api/{customer,internal},adapters,automation}`, `migrations`, `scripts`, `tests`, `frontend`)
- `pyproject.toml` (FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, JWT/bcrypt/pyotp, pytest)
- `src/core/config.py` (pydantic-settings, inkl. Adapter-Provider-Flags, Domain `heihaf.kiste.org`)
- `src/core/database.py` (async Engine/Session-Factory, analog NetAsset)
- `src/main.py` (FastAPI-App mit `/health`)
- `src/models/base.py` (`Base`, `UUIDPKMixin`, `TimestampMixin`)
- Alembic-Setup (`alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`)
- `podman-compose.yml` (Postgres-16-DB-Container, Port 5433, API-Container) + `Dockerfile`
- `.env.example`, `.gitignore`
- Git-Repo initialisiert

**Hinweis**: Lokal ist `podman` nicht installiert (nur `docker`). Die Compose-Datei ist als `podman-compose.yml` benannt und podman-kompatibel; lokale Verifikation erfolgt übergangsweise mit `docker compose -f podman-compose.yml`.
