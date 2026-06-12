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

## Schritt 2: Datenmodell + initiale Migration

- Alle 16 Fachobjekte als SQLAlchemy-2.0-Modelle angelegt (`src/models/{customer,user,leistung,anfrage,angebot,bestellung,signatur,avv,auftrag,leistungsschein,dokument,ereignis,umfrage,status}.py`)
- `src/core/status_codes.py`: 15 kundensichtbare Hauptstatus (`KUNDENSTATUS`/`KUNDENSTATUS_LABELS`), interne Zwischenschritte, die 9 Ereignistyp-Konstanten der Trigger-Tabelle, Benachrichtigungsstufen (`ja`/`optional`/`nein`)
- Drei-Rollen-Modell in `User` (`admin`/`user`/`kunde`, `customer_id` nur für `kunde`), 2FA-Felder (TOTP-Secret, Backup-Codes, `totp_enabled`/`totp_required`)
- Architekturentscheidung: `Anfrage.status_kunde`, `Bestellung.status` (vor Beauftragung) und `Leistungsschein.status_kunde` (nach Beauftragung) verwenden alle einheitlich das `KUNDENSTATUS`-Vokabular für eine durchgängige Kundenstatus-Historie. `Bestellung.status` startet bei `warten_auf_signatur` (eine Bestellung löst direkt eine Signatur aus, ohne Anfrage-/Angebotsprüfung)
- `Anfrage.angebot_id` bewusst ohne DB-FK (UUID-Spalte ohne `ForeignKey`), um eine zyklische FK-Abhängigkeit zwischen `anfragen` und `angebote` (`Angebot.anfrage_id`) zu vermeiden
- `migrations/versions/0001_initial_schema.py`: vollständige manuelle Migration für alle 19 Tabellen (inkl. Indizes/FKs), verifiziert mit `alembic upgrade head` und `alembic downgrade base` + erneutem `upgrade head` (Reversibilität)
- `migrations/versions/0002_seed_status_regeln.py`: Seed der `StatusRegel`-Konfiguration für alle 9 Trigger (Ziel-Status + Benachrichtigungsstufe gemäß Fachkonzept-Trigger-Tabelle, `customer_input_required` immer mit `ja`)

## Schritt 3: Auth (admin/user/kunde) + 2FA

- `src/core/auth.py`: JWT (python-jose) + bcrypt, TOTP-2FA (pyotp) inkl. Backup-Codes, analog NetAsset-Pattern
- `AuthContext` mit `role`, `customer_id`, `totp_enabled`/`totp_required`, Properties `is_internal`/`is_admin`/`needs_2fa_setup`, `require_customer_scope()` für Mandantentrennung
- Zweistufiger Login: `POST /auth/login` → bei aktivem 2FA `mfa_required` + `mfa_token` → `POST /auth/2fa/verify` → `access_token`
- 2FA ist für `admin`/`user` Pflicht (`require_internal`/`require_admin`/`require_role` blockieren mit 403, solange `needs_2fa_setup`), für `kunde` optional
- `src/api/auth.py`: `/auth/login`, `/auth/2fa/verify`, `/auth/me`, `/auth/2fa/setup`, `/auth/2fa/enable`, `/auth/2fa/disable`, `/auth/change-password`
- `src/core/bootstrap.py`: legt beim ersten Start einen `admin`-User an (`totp_required=True`), `src/main.py` ruft dies im `lifespan` auf

## Schritt 5: Adapter-Stubs (Signatur, AVV, Zielsystem, Notification)

- `src/adapters/signature/{base,stub}.py`: `SignatureProvider`-Protokoll (`create_envelope`, `get_status`, `cancel`); Stub erzeugt `Signaturvorgang` mit Link `/sign/{token}`
- `src/adapters/avv/{base,stub}.py`: `AVVWorkflow`-Protokoll (`determine_requirement`, `create_avv`, `get_status`); Stub prüft `Leistung.avv_erforderlich` und stößt über den Signature-Adapter einen Signaturvorgang für die AVV an
- `src/adapters/target_system/{base,stub}.py`: `TargetSystemAdapter`-Protokoll (`push_order`, `update_status`); Stub schreibt `Ereignisprotokoll`-Einträge als Integrationsnachweis
- `src/adapters/notification/{base,stub}.py`: `NotificationProvider.send_email`; Stub loggt
- `src/adapters/registry.py`: `lru_cache`-Factories je Adapter-Typ, gesteuert über `settings.<x>_provider` (Default `"stub"`)

## Schritt 6: Statusautomatisierung (Event-Bus, StatusRegel, Handler)

- `src/services/numbering.py`, `src/services/origin.py`, `src/services/auftrag_service.py`: Hilfsservices – Nummernvergabe, Navigation Angebot→Anfrage/Bestellung (`find_origin_for_angebot`/`set_origin_status`), automatische Anlage von Auftrag + Leistungsschein + Auftragsbestätigung inkl. Anstoß des Zielsystem-Adapters
- `src/automation/rules.py`: lädt `StatusRegel` je Ereignistyp
- `src/automation/dedup.py`: unterdrückt wiederholte „optional“-Benachrichtigungen anhand des letzten `Ereignisprotokoll`-Eintrags zum selben Bezugsobjekt; `ja`-Regeln (z. B. `customer_input_required`) benachrichtigen immer
- `src/automation/handlers.py`: `HANDLERS`-Dict für die 9 Trigger aus der Fachkonzept-Tabelle (`signature_completed`, `avv_required`, `avv_completed`, `kickoff_scheduled`, `onboarding_workshop_scheduled`, `onboarding_workshop_finished`, `customer_input_required`, `delivery_completed`, `survey_sent`); `signature_completed` verzweigt je nach `bezugstyp` (Angebot/AVV/Auftragsbestätigung)
- `src/automation/events.py`: `publish()` schreibt `Ereignisprotokoll`-Eintrag, ruft den passenden Handler, prüft `StatusRegel` + Dedup-Logik und versendet ggf. eine Kundenbenachrichtigung (mit eigenem `notification_sent`-Protokolleintrag)

**Architekturentscheidung**: Der Event-Bus deckt ausschließlich die 9 formal definierten Trigger ab. Alle übrigen Statuswechsel (`anfrage_eingegangen` → `in_pruefung` → `angebot_erstellt` → `warten_auf_signatur`) erfolgen als direkte Feldänderungen durch die noch zu bauenden Workflow-Endpunkte (Schritt 4), nicht über den Event-Bus.

**Verifikation**: `alembic upgrade head` (inkl. Seed 0002) sowie `alembic downgrade base` + `upgrade head` erfolgreich gegen Postgres 16 (Docker); API-Container-Neustart mit `/health` → 200; Import-Check `from src.automation.events import publish; from src.automation.handlers import HANDLERS` im Container erfolgreich (9 Handler registriert).

**Offen**: Schritt 4 (Kern-Workflow-APIs) muss die Event-Publikation noch verdrahten und die direkten Statuswechsel implementieren.
