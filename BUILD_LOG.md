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
