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

## Schritt 4: Kern-Workflows (Katalog, Anfrage, Angebot, Bestellung, AVV, Auftrag, Leistungsschein, Monitoring)

- `src/schemas/`: Pydantic-Schemas für alle 16 Fachobjekte (`catalog`, `customer`, `anfrage`, `angebot`, `bestellung`, `signatur`, `avv`, `auftrag`, `leistungsschein` inkl. `Aufgabe`/`Workshop`, `dokument`, `umfrage`, `ereignis`, `status`); je Domäne reduzierte Kundensicht vs. interne Sicht (z. B. `LeistungsscheinKundenSicht`/`LeistungsscheinInternSicht`, `AnfrageOut`/`AnfrageInternOut`)
- `src/services/signatur_resolve.py`: `resolve_customer_id()` ermittelt den Mandanten eines `Signaturvorgang` anhand von `bezugstyp`/`bezugs_id` (Angebot/Bestellung/AVV/Auftragsbestätigung) für die Mandantenprüfung auf der öffentlichen Signaturseite
- **Architekturerweiterung**: `Bestellung` erhält einen eigenen Signaturfluss analog zum Angebot (`BEZUG_BESTELLUNG` in `src/models/signatur.py`, `_handle_bestellung_signiert` in `src/automation/handlers.py`): Bestellung → Signatur → ggf. AVV-Prüfung → Auftrag + Leistungsschein. `Bestellung.status` nutzt durchgängig das `KUNDENSTATUS`-Vokabular (Default `warten_auf_signatur`), die alten `BESTELLUNG_*`-Konstanten und die Migration 0001 wurden entsprechend angepasst (noch ungepusht, daher ohne neue Migration)
- **Kundensicht** (`src/api/customer/`, alle `require_customer` + `ctx.require_customer_scope`):
  - `catalog.py` – `GET /portal/leistungen` (aktive, bestellbare Leistungen)
  - `bestellungen.py` – `GET/POST /portal/bestellungen`; `POST` legt Bestellung an und stößt sofort einen Signaturvorgang (`BEZUG_BESTELLUNG`) an
  - `anfragen.py` – `GET/POST /portal/anfragen`
  - `angebote.py` – `GET /portal/angebote`, `POST /portal/angebote/{id}/ablehnen` (storniert Signaturvorgang, setzt Ursprung auf `storniert`)
  - `signatur.py` – `GET /portal/signatur/{token}`, `POST /portal/signatur/{token}/signieren` (Stub-Signaturseite, löst `signature_completed` aus)
  - `avv.py` – `GET /portal/avv`, `POST /portal/avv/{id}/annehmen` (löst `avv_completed` aus)
  - `dokumente.py`, `auftraege.py` (inkl. `POST .../auftragsbestaetigung/kenntnisnahme`), `leistungsscheine.py` (reduzierte Sicht inkl. Aufgaben/Workshops), `umfragen.py` (`POST .../beantworten`), `dashboard.py` (Übersicht offener Vorgänge)
  - `src/api/customer/__init__.py` aggregiert alle Router unter `/api/v1/portal`
- **Interne Sicht** (`src/api/internal/`, `require_role("user", "admin")` sofern nicht anders angegeben):
  - `anfragen.py` – Fachbereichszuordnung/Status (`PATCH`), `POST /{id}/angebot` erzeugt Angebot inkl. Positionen und verknüpft die Anfrage
  - `angebote.py` – `POST /{id}/bereitstellen` (Status → `bereitgestellt`, Ursprung → `warten_auf_signatur`, stößt Signaturvorgang für `BEZUG_ANGEBOT` an)
  - `bestellungen.py`, `auftraege.py` (inkl. Auftragsbestätigung) – Monitoring/Read-Only
  - `leistungsscheine.py` – `PATCH` (interne Felder), Aufgaben-CRUD, `POST /{id}/kundenrueckfrage` (→ `customer_input_required`), `POST /{id}/abschliessen` (→ `delivery_completed`, legt automatisch Umfrage an)
  - `workshops.py` – Workshop-CRUD je Leistungsschein; `typ=kickoff` löst beim Anlegen `kickoff_scheduled` aus, `typ=onboarding` beim Anlegen `onboarding_workshop_scheduled` und beim Setzen auf `protokoll_freigegeben` zusätzlich `onboarding_workshop_finished`
  - `avv.py` – Monitoring (`GET /avv`) + `avv-vorlagen`-Verwaltung (admin-only via separatem Sub-Router)
  - `signaturen.py` – Monitoring, `POST /{id}/erinnerung`, `POST /{id}/retry`
  - `monitoring.py` – `GET /uebersicht` (offene Anfragen/Bestellungen/Leistungsscheine, unverarbeitete Ereignisse), `GET /ereignisse` (Filter nach `verarbeitet`/`ereignis_typ`)
  - `kunden.py`, `leistungen.py` (Katalogpflege) – CRUD
  - `umfragen.py` – Reporting (Read-Only)
  - `statusregeln.py`, `users.py` (inkl. Passwort-/2FA-Reset) – admin-only via `require_role("admin")`
  - `src/api/internal/__init__.py` aggregiert alle Router unter `/api/v1/intern`
- `src/main.py`: Kunden- und interne Router eingebunden (insgesamt 70 Endpunkte laut OpenAPI-Schema)

**Verifikation**: API-Container-Neustart ohne Fehler, `/health` → 200, `/openapi.json` listet alle 70 erwarteten Pfade unter `/api/v1/portal/*`, `/api/v1/intern/*` und `/auth/*`. `scripts/e2e_check.py` (manuelles Verifikationsskript, kein Teil der Test-Suite) durchläuft den vollständigen Kernworkflow erfolgreich: Admin-Login mit 2FA-Setup, Anlage Leistung (AVV-Pflicht) + AVV-Vorlage + Kunde + Kunden-User, Bestellung → Signatur → `avv_ausstehend` → AVV-Annahme → `beauftragt` (Auftrag + Leistungsschein automatisch angelegt) → Kick-Off-Workshop (`kickoff_gestartet`) → Onboarding-Workshop (`onboarding_workshop` → Protokollfreigabe → `in_bearbeitung`) → Kundenrückfrage (`warten_auf_kunde`) → Abschluss (`kundenzufriedenheitsabfrage`, Umfrage automatisch versendet) → Umfrage beantwortet → Monitoring-Übersicht zeigt korrekte Zahlen.

## Schritt 7: Frontend-Grundgerüst (Vite/React/Tailwind, Auth, Routing)

- `frontend/`: Vite + React 19 + TypeScript + Tailwind v4 (`@tailwindcss/vite`), React Router v7, TanStack Query v5, lucide-react – Setup analog NetAsset (`package.json`, `vite.config.ts`, `tsconfig*.json`, `eslint.config.js`, `index.html`)
- `vite.config.ts`: Dev-Server-Proxy `/api` und `/auth` → `http://api:8000` (Compose-Servicename), `host: true` für Erreichbarkeit aus dem Container
- `src/api/client.ts`: `req<T>()`-Helper mit Bearer-Token aus `localStorage`, 401-Handling (Token/Rolle löschen + Redirect `/login`); `api.auth` deckt den vollständigen Auth-/2FA-Self-Service ab (`login`, `verify2FA`, `me`, `setup2FA`, `enable2FA`, `disable2FA`, `changePassword`, `logout`); `me()` persistiert `role`/`customer_id` in `localStorage` für rollenbasiertes Routing
- `src/pages/Login.tsx`: zweistufiger Login (Passwort → TOTP-Code/Backup-Code falls `mfa_required`), danach Weiterleitung anhand der Rolle (`kunde` → `/portal`, sonst `/intern`, bzw. `/einstellungen` falls 2FA-Pflicht noch nicht erfüllt)
- `src/pages/Settings.tsx`: Self-Service „Einstellungen“ für alle Rollen – 2FA-Einrichtung (Secret/Provisioning-URI anzeigen, Code bestätigen, Backup-Codes anzeigen), 2FA-Deaktivierung (nur falls `totp_required=false`), Passwortänderung
- `src/components/CustomerLayout.tsx` (Navigation: Übersicht, Katalog, Anfragen, Angebote, AVV, Aufträge, Leistungsscheine, Dokumente, Umfragen) und `src/components/InternalLayout.tsx` (Navigation für `user`/`admin`, admin-only Einträge „Statusregeln“/„Benutzerverwaltung“ nur sichtbar wenn `role=admin`)
- `src/App.tsx`: `AuthGate` lädt `/auth/me` und entscheidet Routing – `kunde` → `CustomerRoutes` (`/portal/*`), `user`/`admin` → `InternalRoutes` (`/intern/*`, admin-only Routen zusätzlich serverseitig per `isAdmin`-Check abgesichert), erzwingt bei `totp_required && !totp_enabled` (admin/user) Redirect auf `/einstellungen` bis 2FA eingerichtet ist
- `src/pages/Placeholder.tsx`: Platzhalterseite für noch nicht implementierte Fachseiten (folgen in Schritt 8/9)
- `Dockerfile.frontend` (Node 22, `npm run dev -- --host`) + `podman-compose.yml`: neuer `frontend`-Service (Port 5173), Named Volume für `node_modules` getrennt vom Bind-Mount des Quellcodes

**Verifikation**: `docker compose -f podman-compose.yml build frontend` erfolgreich; `npx tsc -b` und `npx eslint .` im Container ohne Fehler/Warnungen; `docker compose -f podman-compose.yml up -d` startet `db`/`api`/`frontend` zusammen, Vite-Dev-Server erreichbar unter `:5173`; Proxy-Test bestätigt `/auth/login` und `/api/v1/*` werden korrekt an den `api`-Container weitergeleitet (Login liefert `mfa_required` für den 2FA-pflichtigen Admin-Account).

## Schritt 8: Frontend Kundensicht

- `src/lib/format.ts`: Formatierungshelfer `formatCurrency` (EUR, `de-DE`), `formatDate`/`formatDateTime` (`de-DE`, Fallback `–` bei `null`/`undefined`)
- `src/components/StatusBadge.tsx`: Badge-Komponente für alle 15 `KUNDENSTATUS`-Werte mit deutschem Label und Farbcodierung (slate/indigo/amber/sky/emerald/red)
- `src/pages/customer/Dashboard.tsx` (`/portal`): Übersicht „Offene Bestellungen“, „Offene Anfragen“, „Laufende Leistungsscheine“ (mit Link zur Detailseite) via `GET /portal/dashboard`
- `src/pages/customer/Katalog.tsx` (`/portal/katalog`): Leistungskatalog als Kartenraster (Name, Kategorie, Beschreibung, Preis, AVV-Pflicht-Hinweis), „Bestellen“ löst `POST /portal/bestellungen` aus und navigiert zu „Aufträge“
- `src/pages/customer/Anfragen.tsx` (`/portal/anfragen`): Formular „Neue Anfrage“ (Thema, Beschreibung, Fachbereich, Priorität) via `POST /portal/anfragen` sowie Liste „Meine Anfragen“ mit `StatusBadge`
- `src/pages/customer/Angebote.tsx` (`/portal/angebote`): Angebotsdetails inkl. Positionstabelle und Gesamtpreis; bei Status `bereitgestellt` Ermittlung des zugehörigen Signaturvorgangs über das neue Endpoint `GET /portal/signatur/by-bezug/{bezugstyp}/{bezugs_id}` und Anzeige von „Zur Signatur“-Link bzw. „Ablehnen“-Button (`POST /portal/angebote/{id}/ablehnen`)
- `src/pages/customer/AVV.tsx` (`/portal/avv`): Liste aller AVV-Vorgänge mit Status-Icons, „AVV annehmen“-Button bei Status `ausstehend` (`POST /portal/avv/{id}/annehmen`)
- `src/pages/customer/Auftraege.tsx` (`/portal/auftraege`): Auftragsliste mit `StatusBadge`; pro Auftrag wird die Auftragsbestätigung über das neue Endpoint `GET /portal/auftraege/{id}/auftragsbestaetigung` geladen und ggf. ein „Zur Kenntnis nehmen“-Button (`POST .../kenntnisnahme`) angezeigt
- `src/pages/customer/Leistungsscheine.tsx` (`/portal/leistungsscheine`): Listenansicht (Nummer, Scope-Beschreibung, Solltermin, `StatusBadge`), verlinkt auf Detailseite
- `src/pages/customer/LeistungsscheinDetail.tsx` (`/portal/leistungsscheine/:id`): Detailansicht mit allgemeinen Feldern (Termine, nächster Schritt, Voraussetzungen, Onboarding-Ziele/offene Punkte), Aufgabenliste (Status-Labels `offen`/`in_bearbeitung`/`erledigt`/`blockiert`) und Workshop-Liste (Typ `kickoff`/`onboarding`, Status `geplant`/`durchgefuehrt`/`protokoll_freigegeben`/`verschoben`)
- `src/pages/customer/Dokumente.tsx` (`/portal/dokumente`): Liste aller für den Kunden sichtbaren Dokumente (Dateiname, Typ, Erstellungsdatum)
- `src/pages/customer/Umfragen.tsx` (`/portal/umfragen`): Liste der Kundenzufriedenheitsabfragen; unbeantwortete Umfragen mit Stern-Bewertung (1-5) + optionalem Kommentar via `POST /portal/umfragen/{id}/beantworten`, beantwortete Umfragen read-only
- `src/pages/customer/Signatur.tsx` (`/portal/signatur/:token`): Stub-Signaturseite – zeigt Status (`erstellt`/`versendet`/`signiert`/`abgelehnt`/`fehler`/`abgelaufen`) und bei `erstellt`/`versendet` einen „Jetzt signieren“-Button (`POST /portal/signatur/{token}/signieren`)
- `src/App.tsx`: alle `<Placeholder>`-Routen unter `/portal/*` durch die neuen Seiten ersetzt, neue Routen `/portal/leistungsscheine/:id` und `/portal/signatur/:token` ergänzt

### Neue Backend-Endpunkte (API-Lückenschluss für Frontend)

- `src/api/customer/signatur.py`: `GET /portal/signatur/by-bezug/{bezugstyp}/{bezugs_id}` – ermittelt Signaturvorgänge zu einem Angebot/einer Bestellung (mandantengeprüft), damit das Portal den Signatur-Token zum Anzeigen des „Zur Signatur“-Links auflösen kann
- `src/api/customer/auftraege.py`: `GET /portal/auftraege/{auftrag_id}/auftragsbestaetigung` – liefert die Auftragsbestätigung zu einem Auftrag (mandantengeprüft, 404 falls noch nicht erstellt), Pendant zum internen Endpoint

**Verifikation**: `npx tsc -b` und `npx eslint .` im `frontend`-Container ohne Fehler/Warnungen; `docker compose -f podman-compose.yml up -d db api frontend` startet alle drei Container fehlerfrei, Vite-Dev-Server liefert weiterhin unter `:5173`.

## Schritt 9: Frontend interne Sicht

Alle Routen unter `/intern/*` (für die Rollen `user` und `admin`) mit echten Seiten ersetzt, analog zur Kundensicht aus Schritt 8.

### Neue gemeinsame Konstanten

- `src/lib/statuscodes.ts`: zentrale Quelle für Status-Vokabulare und deutsche Labels, gespiegelt aus `src/core/status_codes.py`. Exportiert `KUNDENSTATUS` (15 Werte) + `KUNDENSTATUS_LABELS`, `INTERNE_ZWISCHENSCHRITTE` (17 Werte), `PRIORITAET_OPTIONS`, sowie Label-Maps für Aufgabe, Workshop (Status/Typ), Angebot, AVV und Signatur. `src/components/StatusBadge.tsx` und mehrere Kundensicht-Seiten (`Angebote.tsx`, `AVV.tsx`) wurden refaktoriert, um ihre lokalen Label-Maps durch Importe aus dieser Datei zu ersetzen (vermeidet Duplikation, behebt zugleich einen `react-refresh/only-export-components`-Lint-Fehler in `StatusBadge.tsx`).

### Erweiterung `src/api/client.ts`

Neuer Namespace `api.intern` mit vollständiger Abdeckung aller 14 internen Teilbereiche (Anfragen, Angebote, Bestellungen, Aufträge, Leistungsscheine inkl. Aufgaben/Workshops, AVV inkl. Vorlagen, Signaturen, Monitoring, Kunden, Leistungen, Umfragen, Statusregeln, Benutzerverwaltung) sowie ~22 neue TypeScript-Interfaces (`AnfrageIntern`, `AngebotCreate`, `LeistungsscheinIntern`, `AufgabeCreate`/`Update`, `WorkshopCreate`/`Update`, `AVVVorlage`, `Customer`, `InternUser`, `StatusRegel`, `Ereignis`, `MonitoringUebersicht`, …).

### Neue interne Seiten (`src/pages/internal/`)

- `Dashboard.tsx` (`/intern`): 4 Kennzahlen-Karten (offene Anfragen/Bestellungen, laufende Leistungsscheine, unverarbeitete Ereignisse) via `GET /intern/monitoring/uebersicht`
- `Anfragen.tsx` (`/intern/anfragen`): aufklappbare Liste je Anfrage mit Bearbeitungsformular (Fachbereich, Priorität, interner Zwischenschritt, Kundenstatus) via `PATCH /intern/anfragen/{id}`; Link zu „Angebot erstellen“ bzw. „Angebot ansehen“
- `AngebotErstellen.tsx` (`/intern/anfragen/:id/angebot`): Formular zur Angebotserstellung mit dynamischer Positionsliste, `POST /intern/anfragen/{id}/angebot`
- `Angebote.tsx` (`/intern/angebote`): Angebotsliste mit Positionstabelle, Gesamtpreis, `StatusBadge`; „Bereitstellen“-Button bei Status `entwurf` (`POST /intern/angebote/{id}/bereitstellen`)
- `Bestellungen.tsx` (`/intern/bestellungen`): read-only Liste (Bestellnummer, Datum, `StatusBadge`)
- `Auftraege.tsx` (`/intern/auftraege`): Liste mit Auftragsbestätigungsstatus (`GET /intern/auftraege/{id}/auftragsbestaetigung`) und Link zu Leistungsscheinen
- `Leistungsscheine.tsx` (`/intern/leistungsscheine`): Listenansicht mit Link zur Detailseite
- `LeistungsscheinBearbeitung.tsx` (`/intern/leistungsscheine/:id`): vollständige Bearbeitungsseite – allgemeine Felder (Scope, Termine, Status, nächster Schritt, Voraussetzungen, Onboarding-Ziele/offene Punkte, Lessons Learned), Buttons „Kundenrückfrage senden“ (`POST .../kundenrueckfrage`) und „Abschließen“ (`POST .../abschliessen`), Aufgabenverwaltung (anlegen/bearbeiten/löschen über `/intern/leistungsscheine/{id}/aufgaben*`) und Workshopverwaltung (anlegen/bearbeiten über `/intern/leistungsscheine/{id}/workshops*`)
- `AVV.tsx` (`/intern/avv`): Liste aller AVV-Vorgänge (`StatusBadge`); admin-only Abschnitt „AVV-Vorlagen“ mit Aktiv/Inaktiv-Toggle und Anlegen-Formular (`/intern/avv-vorlagen`)
- `Signaturen.tsx` (`/intern/signaturen`): Liste mit `SIGNATUR_STATUS_LABELS`, „Erinnerung“-Button bei `versendet` (`POST .../erinnerung`), „Erneut versenden“ bei `fehler`/`abgelaufen` (`POST .../retry`)
- `Umfragen.tsx` (`/intern/umfragen`): read-only Reporting-Liste mit Bewertung/Kommentar
- `Monitoring.tsx` (`/intern/monitoring`): Kennzahlen-Karten + Ereignisliste mit Filter „Nur unverarbeitete“ (`GET /intern/monitoring/ereignisse`)
- `Kunden.tsx` (`/intern/kunden`): Kundenverwaltung – Liste, Anlegen-Formular, Aktiv/Inaktiv-Toggle
- `Leistungen.tsx` (`/intern/leistungen`): Katalogpflege – Liste, Anlegen-Formular, Toggle für AVV-Pflicht und Aktiv/Inaktiv
- `Statusregeln.tsx` (`/intern/statusregeln`, admin-only): Liste aller `StatusRegel`-Einträge mit editierbarem Zielstatus (Kundensicht), Benachrichtigungsstufe (`ja`/`optional`/`nein`) und Aktiv-Flag
- `Benutzer.tsx` (`/intern/benutzer`, admin-only): Benutzerverwaltung – Liste, Anlegen-Formular (inkl. Kundenzuordnung bei Rolle `kunde`), Passwort-Reset, 2FA-Reset, Aktiv/Inaktiv-Toggle

### `src/App.tsx`

Alle `<Placeholder>`-Routen unter `/intern/*` durch die neuen Seiten ersetzt, neue Route `/intern/anfragen/:id/angebot` und `/intern/leistungsscheine/:id` ergänzt. Import von `Placeholder` entfernt (nicht mehr verwendet).

**Verifikation**: `npx tsc -b` und `npx eslint .` im `frontend`-Container ohne Fehler/Warnungen; `docker compose -f podman-compose.yml up -d db api frontend` startet alle drei Container fehlerfrei, Vite-Dev-Server liefert weiterhin unter `:5173`.

## Schritt 10: Demo-/Seed-Daten

- `scripts/seed_demo_data.py`: async Seed-Skript, das einen reproduzierbaren Demo-Bestand anlegt und dabei den Fachprozess über denselben Event-Bus (`src.automation.events.publish`) durchspielt, den auch die API nutzt – die erzeugten Statusübergänge entsprechen damit exakt dem Produktivverhalten.
  - **StatusRegeln**: legt fehlende Regeln für alle 9 Trigger an (idempotent; die Basis-Konfiguration kommt bereits aus Migration `0002`, das Skript ergänzt nur Lücken)
  - **AVV-Vorlage**: eine aktive „Standard-AVV (Art. 28 DSGVO)“
  - **Katalog**: 5 Leistungen (Managed Workplace/Backup mit AVV-Pflicht, IT-Sicherheitsaudit, Microsoft-365-Einführung, Support-Kontingent)
  - **Benutzer**: `admin` (2FA-Pflicht), `mitarbeiter` (Rolle `user`, 2FA-Pflicht), `kunde1`/`kunde2` (Rolle `kunde`); Demo-Passwörter werden am Ende ausgegeben
  - **Kunden**: „Nordlicht Logistik GmbH“ (K-1001) und „Alpenblick Steuerberatung“ (K-1002), je mit Kontakt-E-Mail (damit der Notification-Stub greift)
  - **Offene Anfrage**: eine Anfrage im Status `in_pruefung` für Kunde 2
  - **Vollständiger Durchlauf** für Kunde 1 (Managed Workplace, AVV-pflichtig): Bestellung → Signatur (`signature_completed`) → AVV ausstehend (`avv_required`) → AVV angenommen (`avv_completed`) → automatisch angelegter Auftrag + Leistungsschein (`beauftragt`) → Kick-Off-Workshop (`kickoff_gestartet`) → Onboarding-Workshop (`onboarding_workshop`) → Protokoll freigegeben (`onboarding_workshop_finished` → `in_bearbeitung`); zusätzlich 3 Aufgaben in den Status `erledigt`/`in_bearbeitung`/`offen`
- Idempotenz: das Skript bricht ab, wenn Kunde `K-1001` bereits existiert.

**Verifikation**: `alembic downgrade base && alembic upgrade head` läuft fehlerfrei durch (Reversibilität bestätigt; Migration `0002` seedet die StatusRegel-Konfiguration). `python scripts/seed_demo_data.py` im `api`-Container legt den Bestand an; Kontrolle per `psql` bestätigt Leistungsschein `LS-2026-0001` im Status `in_bearbeitung`, zwei Workshops (`kickoff`=geplant, `onboarding`=protokoll_freigegeben), drei Aufgaben, AVV `abgeschlossen`, Anfrage `in_pruefung`. Zweiter Aufruf bricht idempotent ab.

## Schritt 11: Deployment-Vorbereitung (Podman/Caddy)

Produktions-Stack, der – anders als `podman-compose.yml` (Entwicklung mit Hot-Reload/Code-Volumes) – alle Images aus dem Quellcode baut und ohne Code-Mounts läuft.

- `scripts/entrypoint.sh`: Produktions-Entrypoint des API-Containers – führt `alembic upgrade head` aus, optional `seed_demo_data.py` bei `SEED_DEMO_DATA=true`, startet dann `uvicorn` ohne `--reload`. In der `Dockerfile` per `chmod +x` ausführbar gemacht.
- `Caddyfile`: Reverse-Proxy für `{$DOMAIN}` (aus `.env`). Backend-Pfade (`/api/*`, `/auth/*`, `/health`, `/docs`, `/openapi.json`, `/redoc`) → `api:8000`; alles andere als statisches SPA-Frontend mit History-Fallback auf `index.html`. Echter Domainname → automatisches Let's-Encrypt-TLS; `DOMAIN=:80` für lokale Tests ohne TLS. Da der Frontend-API-Client relative Pfade (`/api/v1`, `/auth`) nutzt, ist kein Build-Zeit-API-URL-Konfig nötig.
- `Dockerfile.caddy`: Multi-Stage-Build – Stage 1 baut das Vite-Frontend (`npm run build` → `dist/`), Stage 2 (`caddy:2-alpine`) übernimmt `dist/` nach `/srv` und die `Caddyfile`. Ein einziges Image liefert Frontend **und** Reverse-Proxy.
- `podman-compose.prod.yml`: Services `db` (PostgreSQL 16, kein Host-Port, persistentes Volume, `restart: unless-stopped`), `api` (Build aus `Dockerfile`, Entrypoint mit Migrationen, Secrets aus `.env` via `${VAR:?}`-Pflichtprüfung), `caddy` (Ports 80/443, Volumes `caddy_data`/`caddy_config` für Zertifikate). DB-URL wird im Prod-Stack aus `POSTGRES_*` zusammengesetzt.
- `.env.example`: um die Prod-Variablen `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` und `SEED_DEMO_DATA` erweitert; Hinweis auf `DOMAIN=:80` für lokale Tests.

**Verifikation**: Voller Prod-Stack lokal gebaut und gestartet (`docker compose -f podman-compose.prod.yml ... up -d --build`, Caddy-Port testweise auf `8080` gemappt, `DOMAIN=:80`). API-Entrypoint führte Migrationen + Demo-Seed aus und startete den Server. Über Caddy verifiziert: `GET /health` → `200 {"status":"ok"}`, `GET /api/v1/portal/leistungen` ohne Token → `401`, `GET /docs` → `200`, `GET /` liefert die SPA (`<title>Kundenportal Heimathafen</title>`), Deep-Link `/intern/kunden` → `200` (History-Fallback). End-to-End: `POST /auth/login` (kunde1) liefert JWT, autorisierter `GET /api/v1/portal/leistungsscheine` liefert den mandantengefilterten Leistungsschein `LS-2026-0001`. Anschließend Stack inkl. Volumes wieder abgebaut.

## Schritt 12: End-to-End-Verifikation (pytest-Integrationstests)

Automatisierte Integrationstests gegen die laufende API (httpx + pytest-asyncio), die die Verifikationspunkte des Plans abdecken. Liegen unter `tests/` (`conftest.py` + `test_integration.py`), laufen gegen `BASE_URL` (Default `http://localhost:8000`) und setzen eine frische DB voraus (einmaliges Admin-2FA-Setup, dessen TOTP-Secret sich nicht wiederherstellen lässt).

- `tests/conftest.py`: session-scoped Fixtures – `client` (httpx), `admin_token` (Admin-Login inkl. einmaligem 2FA-Setup/Enable via `pyotp` + Re-Login über `mfa_required`/`verify`), Hilfsfunktionen `_enable_2fa`/`_login_with_2fa`/`unique`. Admin-Passwort aus `INITIAL_ADMIN_PASSWORD` (Default `change-me`).
- `tests/test_integration.py` (9 Tests):
  - **2FA/Login je Rolle**: Admin mit aktivem 2FA, Kunde ohne 2FA-Zwang, interner `user` mit 2FA-Setup
  - **2FA-Gating**: interner `user` ohne aktiviertes 2FA wird auf internen Endpunkten mit `403` geblockt
  - **Rollenprüfung**: `user` darf operative Endpunkte (`/intern/anfragen`, `/intern/monitoring/uebersicht`), aber nicht die admin-only Endpunkte (`/intern/statusregeln`, `/intern/users`, `/intern/avv-vorlagen` → `403`); Admin darf alle; Kunde wird auf internen Endpunkten geblockt
  - **Mandantentrennung**: Kunde B erhält `404` auf Bestellung bzw. AVV-Annahme von Kunde A
  - **Vollständiger Workflow inkl. aller 9 Trigger**: Bestellung → Signatur (`signature_completed`) → `avv_required` → AVV-Annahme (`avv_completed`) → Auftrag+Leistungsschein (`beauftragt`) → Kick-Off (`kickoff_scheduled`) → Onboarding (`onboarding_workshop_scheduled`) → Protokoll (`onboarding_workshop_finished` → `in_bearbeitung`) → Kundenrückfrage (`customer_input_required` → `warten_auf_kunde`) → Abschluss (`delivery_completed`/`survey_sent` → `kundenzufriedenheitsabfrage`) → automatisch angelegte Umfrage wird vom Kunden beantwortet
  - **API-Abdeckung**: prüft, dass alle Teilbereiche (Kundensicht + interne Sicht) im OpenAPI-Schema (`/openapi.json`) vorhanden sind
- `pyproject.toml`: `asyncio_default_fixture_loop_scope = "session"` ergänzt (session-weiter Event-Loop für die Fixtures unter pytest-asyncio 1.x).

**Verifikation**: Auf frischer DB (`alembic downgrade base && alembic upgrade head`, API-Neustart für Bootstrap-Admin) laufen alle 9 Tests grün durch (`python -m pytest tests/ -q` → `9 passed`), sowohl mit explizitem `INITIAL_ADMIN_PASSWORD` als auch out-of-the-box mit dem Default. Reversibilität der Migrationen (`downgrade base`/`upgrade head`) dabei erneut bestätigt. Frontend-Verifikation (`npx tsc -b`, `npx eslint .`, Prod-Build via `Dockerfile.caddy`) bereits in Schritt 9 bzw. 11 erfolgt.

---

**Stand:** Alle 12 Schritte des Implementierungsplans abgeschlossen. Das Kundenportal deckt den kompletten Fachprozess (Anfrage → Angebot → Beauftragung → AVV → Auftrag → Leistungsschein mit Workshops/Aufgaben → Umfrage) mit voller API-Abdeckung je Teilbereich, Adapter-Stubs (Signatur/AVV/Zielsystem/Notification), Statusautomatisierung, 2FA für drei Rollen und einem Podman/Caddy-Produktions-Setup ab.

## Nachtrag: VPS-Deployment mit reinem Podman (ohne compose)

Für die Installation auf einem externen Linux-VPS ohne `podman-compose` – stattdessen mit reinen `podman`-Kommandos – kam ein eigenständiges Deployment-Verzeichnis hinzu:

- `deploy/kundenportal.sh`: parametrierbares Start-/Verwaltungsskript. Startet die drei Container (`<projekt>-db`, `<projekt>-api`, `<projekt>-caddy`) in einem gemeinsamen Podman-Netzwerk mit festen DNS-Aliasen `db`/`api`/`caddy` (passend zu `Caddyfile` → `api:8000` und `DATABASE_URL` → `db:5432`). Befehle: `up`, `down`, `restart`, `update` (Redeploy nach `git pull`), `build`, `status`, `logs [db|api|caddy]`, `migrate`, `seed`, `destroy`, `install-service` (erzeugt eine systemd-Unit für Autostart). Konfiguration aus `deploy/kundenportal.env` (überschreibbar via `--env-file`); Pflichtwerte werden geprüft. Der API-Container wird mit `--entrypoint /app/scripts/entrypoint.sh` gestartet, damit auch unter Podman die Migrationen vor dem Serverstart laufen; alle Container laufen mit `--restart=always`.
- `deploy/kundenportal.env.example`: Konfigurationsvorlage (DOMAIN, POSTGRES_*, JWT_SECRET, INITIAL_ADMIN_PASSWORD, Adapter-Provider, Ports, SEED_DEMO_DATA, Projekt-/Image-Namen).
- `deploy/README.md`: Schritt-für-Schritt-Anleitung für den VPS (Podman-Installation, Repo holen, konfigurieren, `up`, systemd-Autostart, Update, Backup, Rootless-Ports-Hinweise).
- `.gitignore`: `deploy/kundenportal.env` und weitere `deploy/*.env` (Secrets) ausgenommen, nur die `.example`-Vorlage wird versioniert.

**Verifikation**: `bash -n` (Syntax) fehlerfrei; Skriptlogik (Argument-Parsing, Laden/Validieren der Env-Datei, Ableiten der Namen, Reihenfolge `network → volumes → build → db → wait_for_db → api → caddy`, korrekt aufgebaute `podman run`-Kommandos inkl. `--entrypoint`, `--network-alias`, Port-Mappings und `DATABASE_URL=…@db:5432`) gegen ein `podman`-Stub-Skript geprüft; Pflichtwert-Prüfung bricht mit klarer Meldung ab. (Realer Podman-Lauf erfolgt auf dem Ziel-VPS.)

## Nachtrag: Echte Signaturen (In-Portal, signature_provider=inhouse)

Recherche (Open-Source, eIDAS): self-hosted Plattformen wie OpenSign/DocuSeal bieten die API/Webhooks nur im kostenpflichtigen Plan an; die kostenlose Self-Host-Version ist nicht per API automatisierbar. Da EES/FES als Rechtsstufe ausreicht, wurde eine **leichtgewichtige In-Portal-Lösung ohne Zusatzdienst** umgesetzt – sie fügt sich als zweiter `SignatureProvider` hinter den bestehenden Adapter (`signature_provider=stub|inhouse`).

- **Ablauf**: Der Kunde zeichnet auf der Signaturseite (`/portal/signatur/:token`) seine Unterschrift auf einem Canvas und gibt seinen Namen ein. Das Backend erzeugt daraus ein PDF (Dokumentdaten + eingebettete handschriftliche Unterschrift + Audit-Trail: Name, Zeitstempel, IP, Vorgangs-ID) und **versiegelt es kryptografisch (PAdES) mit pyHanko** (manipulationssicher = FES). Das signierte PDF wird als kundensichtbares Dokument abgelegt und ist unter „Dokumente“ herunterladbar.
- **Nur Open-Source-Bibliotheken**: `reportlab` (PDF), `pyhanko` (PAdES-Versiegelung), `pillow` (Unterschrift-Bild), `cryptography` (selbstsigniertes Siegel-Zertifikat); Frontend `signature_pad` (Canvas).
- **Siegel-Zertifikat**: ist kein eigenes Zertifikat (`SIGNING_CERT_PATH`) konfiguriert, wird beim ersten Signieren automatisch ein selbstsigniertes PKCS#12 unter `<DOCUMENTS_DIR>/../signing/` erzeugt und wiederverwendet. Die Unterzeichner-Identität ergibt sich aus Login + Audit-Trail.

### Geänderte/neue Dateien

- `src/services/pdf_signing.py` (neu): `ensure_signing_pkcs12()` (Self-Signed-Zertifikat), `build_signature_pdf()` (reportlab), `seal_pdf()` (pyHanko PAdES), `erzeuge_signiertes_pdf()` (Orchestrierung + Ablage).
- `src/adapters/signature/inhouse.py` (neu): `InhouseSignatureProvider` – `create_envelope`/`get_status`/`cancel` wie der Stub plus `apply_signature()`, das je Bezugstyp (Angebot/Bestellung/AVV/Auftragsbestätigung) den Dokumentinhalt aufbaut, das versiegelte PDF erzeugt (CPU-/Krypto-Arbeit via `asyncio.to_thread`, da pyHanko intern `asyncio.run` nutzt) und ein `Dokument` anlegt.
- `src/adapters/signature/base.py` + `stub.py`: Protokoll um `apply_signature()` erweitert (Stub = no-op).
- `src/adapters/registry.py`: `signature_provider=inhouse` registriert.
- `src/core/config.py`: `documents_dir`, `signing_cert_path`, `signing_cert_password`.
- `src/api/customer/signatur.py`: Signier-Endpoint nimmt optionalen Body (`signatur_bild`, `unterzeichner_name`), erfasst die IP (X-Forwarded-For), ruft `apply_signature`; beim inhouse-Provider ist die Unterschrift Pflicht (422).
- `src/api/customer/dokumente.py`: `GET /portal/dokumente/{id}/download` (FileResponse, mandantengeprüft).
- `src/schemas/signatur.py`: `SignaturInput`.
- Frontend: `Signatur.tsx` (Canvas via `signature_pad`, Branch auf `anbieter='inhouse'`), `Dokumente.tsx` (Download-Button, Blob-Download mit Auth-Header), `client.ts` (`signieren(token, payload)`, `dokumente.download`).
- Deployment: `documents_dir` als persistentes Volume (`kundenportal_documents` → `/app/data`) in `podman-compose.prod.yml` und `deploy/kundenportal.sh`; `.env.example`/`deploy/*.env.example` um `SIGNATURE_PROVIDER=inhouse`, `DOCUMENTS_DIR`, `SIGNING_CERT_*` erweitert; `.gitignore` ignoriert `data/`.

**Verifikation**: Inhouse-Provider real gegen die DB getestet (`tests/test_signatur_inhouse.py`) – `apply_signature` erzeugt ein `signatur_dokument` (sichtbarkeit `kunde`) mit gültigem, **einfach signiertem** PDF (pyHanko liest genau eine eingebettete Signatur `KundenportalSignatur`). Gesamte Test-Suite grün (`10 passed`), Stub-Signierpfad der bestehenden Integrationstests unverändert. Frontend `npx tsc -b` + `npx eslint .` ohne Fehler. API-Image frisch gebaut – `reportlab`/`pyhanko`/`pillow`/`cryptography` sind im Image enthalten.

### Nachtrag: Signaturen in der internen Sicht verankert

- `src/api/internal/dokumente.py` (neu, admin/user): `GET /intern/dokumente` (alle Mandanten, optional gefiltert nach `bezugstyp`/`bezugs_id`/`customer_id`) und `GET /intern/dokumente/{id}/download` (FileResponse). In `src/api/internal/__init__.py` registriert.
- `frontend/src/api/client.ts`: `intern.dokumente.list(params)` + `intern.dokumente.download(id, name)` (Blob-Download mit Auth-Header).
- `frontend/src/pages/internal/Signaturen.tsx`: pro Vorgang zusätzlich
  - **„Link"** (bei `versendet`/`erstellt`): kopiert den kundenseitigen Signatur-Link `…/portal/signatur/{token}` in die Zwischenablage – so kann der interne Mitarbeiter „zur Signatur senden“ sichtbar nachvollziehen/weiterleiten,
  - **„Beleg"** (bei `signiert` + `anbieter=inhouse`): lädt das signierte, versiegelte PDF herunter (ermittelt über `intern.dokumente.list({bezugstyp, bezugs_id})`),
  - sowie Anzeige des Signaturzeitpunkts.

**Verifikation**: Neue Routen im OpenAPI-Schema vorhanden (Coverage-Test um `/api/v1/intern/dokumente` erweitert); Test-Suite weiterhin `10 passed`; Frontend `tsc`/`eslint` fehlerfrei.

---

**Stand:** Das Kundenportal bietet damit echte In-Portal-Signaturen (FES) inkl. interner Sichtbarkeit (Signatur-Link kopieren, signierten Beleg herunterladen) – wahlweise per `SIGNATURE_PROVIDER` aktivierbar (`stub` ↔ `inhouse`), ohne externen Dienst.

---

### Angebot-Editor (Entwürfe bearbeiten)

- `src/schemas/angebot.py`: `AngebotUpdate` (Titel, Gültigkeit, Positionen – alle optional).
- `src/api/internal/angebote.py`: `PATCH /intern/angebote/{id}` – bearbeitet nur Status `entwurf` (sonst 409, da ab `bereitgestellt` ein Signatur-Envelope existiert); Positionen werden ersetzt, `gesamtpreis` neu berechnet.
- Frontend: `AngebotBearbeiten.tsx` (eigene Seite, Route `/intern/angebote/:id/bearbeiten`, Positions-Editor wie beim Anlegen, Guard für Nicht-Entwürfe), „Bearbeiten“-Button auf Entwurf-Zeilen in `Angebote.tsx`, `intern.angebote.update()` + `AngebotUpdate` im `client.ts`.

### Anfrage-Ablaufplan (horizontaler Stepper)

- `frontend/src/components/AnfrageAblaufplan.tsx`: horizontale Kachelreihe der verdichteten Workflow-Phasen (Anfrage → Angebot → Signatur → AVV → Beauftragt → Leistungsschein → Umfrage → Abgeschlossen). Erledigte Phasen sky-gefärbt mit Häkchen, aktuelle Phase mit Ring hervorgehoben, künftige gedämpft; Klick auf eine Kachel springt zur passenden internen Seite (Anfrage-Kachel klappt das Detail auf). Stufe abgeleitet aus `status_kunde` über das `KUNDENSTATUS`-Modell.
- In `Anfragen.tsx` unter dem Zeilenkopf eingebunden (immer sichtbar).

> Hinweis: `tsc -b`/`eslint` für diese beiden Schritte auf Wunsch noch nicht ausgeführt.
> Nachgeholt in `fa848a1` (zwei Befunde behoben).

### Fix: Signatur-Link lief ins Leere (Redirect-Ziel durch den Login)

Problem: Der intern kopierte Signatur-Link `…/portal/signatur/{token}` führte beim
kalten Öffnen ins Leere. Ursache: die gesamte App liegt hinter `AuthGate`; ohne
Token wurde hart auf `/login` umgeleitet, **ohne das Ziel zu merken** – nach dem
Login landete man im Dashboard, nie zurück bei der Signatur. Entscheidung:
Signatur bleibt **login-pflichtig** (nur eingeloggte Kunden), aber das Ziel wird
durch den Login mitgeführt.

- `frontend/src/App.tsx`: `AuthGate` hängt bei fehlendem Token das aktuelle Ziel
  als `?redirect=<pfad>` an die Login-URL.
- `frontend/src/pages/Login.tsx`: liest `redirect` aus den Query-Params und
  navigiert nach erfolgreichem Login dorthin (nur interne Pfade zugelassen –
  kein offener Redirect); sonst rollenbasierter Default.
- `frontend/src/api/client.ts`: der 401-Handler führt das Ziel ebenfalls als
  `?redirect=` mit (abgelaufener Token mitten in der Sitzung) und vermeidet eine
  Login-Schleife, wenn man bereits auf `/login` ist.
- `frontend/src/pages/customer/Signatur.tsx`: Fehlerzustand (statt endlosem
  „Lade…“) wenn der Vorgang nicht abrufbar ist (ungültiger Link / fremder
  Mandant), inkl. `retry: false`.

**Verifikation**: Frontend `tsc -b` + `eslint` fehlerfrei (im node:20-Container,
da lokal kein Stack/Node lief). Live-Klicktest steht noch aus.
