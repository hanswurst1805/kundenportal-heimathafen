# Projekt auf einen anderen Rechner umziehen (Claude Code)

Der gesamte Code liegt im GitHub-Repo. Nur drei Dinge liegen **nicht** in Git und
müssen separat übertragen werden:

| Bestandteil | Wo | Transfer |
|---|---|---|
| `.env` (Dev-Secrets) | lokal, gitignored | neu aus `.env.example` anlegen oder kopieren |
| `data/` (signierte PDFs + Siegelzertifikat) | lokal, gitignored | optional kopieren (siehe unten) |
| Memory (`~/.claude/projects/<pfad>/memory/`) | lokal beim alten Rechner | Ordner kopieren bzw. Dateien neu anlegen |

`CLAUDE.md`, `BUILD_LOG.md` und `deploy/README.md` sind im Repo — die neue
Claude-Code-Instanz hat damit vollen Projektkontext.

## Voraussetzungen (neuer Rechner)

- Git
- Podman (+ `podman compose`) oder Docker — die App läuft komplett in Containern
- Claude Code CLI

## 1. GitHub-Zugang einrichten

Repo (privat): `git@github.com:hanswurst1805/kundenportal-heimathafen.git`
(Account **hanswurst1805**).

**SSH (empfohlen):**
```bash
ssh-keygen -t ed25519 -C "deine-email@example.com"
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub      # -> GitHub: Settings > SSH and GPG keys > New SSH key
ssh -T git@github.com          # muss "Hi hanswurst1805!" zeigen
```

**Alternative HTTPS:** Personal Access Token (Scope `repo`) erstellen und beim
`clone` als Passwort verwenden.

## 2. Klonen

```bash
git clone git@github.com:hanswurst1805/kundenportal-heimathafen.git
cd kundenportal-heimathafen
```

## 3. Konfiguration anlegen (Secrets, nicht in Git)

```bash
cp .env.example .env          # INITIAL_ADMIN_PASSWORD, JWT_SECRET, ggf. SIGNATURE_PROVIDER=inhouse
# Für Produktion zusätzlich:
cp deploy/kundenportal.env.example deploy/kundenportal.env   # DOMAIN, POSTGRES_PASSWORD, ...
```

`data/` wird automatisch neu erzeugt. Nur wenn das **gleiche Signatur-Siegel**
weiterverwendet werden soll, vom alten Rechner
`data/signing/kundenportal-signing.p12` an dieselbe Stelle kopieren.

## 4. Starten & prüfen

```bash
podman compose -f podman-compose.yml up -d db api frontend
podman compose -f podman-compose.yml exec api alembic upgrade head
podman compose -f podman-compose.yml exec api python scripts/seed_demo_data.py   # optional
```

Frontend: http://localhost:5173 · API-Doku: http://localhost:8000/docs

Tests:
```bash
podman compose -f podman-compose.yml exec api sh -c "pip install -q '.[dev]' pyotp && python -m pytest tests/ -q"
```

## 5. Memory übertragen

Claude Code legt Memory pro **Startverzeichnis** ab; der Ordnername ist der Pfad
mit `/` ersetzt durch `-`, z. B.
`~/.claude/projects/-Users-kiste-Documents-Claude-Projects/memory/`.

- **Gleicher Pfad/Username:** den kompletten `memory/`-Ordner 1:1 auf den neuen
  Rechner kopieren.
- **Anderer Pfad:** Claude Code einmal im neuen Projektordner starten (legt den
  `memory/`-Ordner an), dann die Dateien dort einfügen — oder die neue Instanz
  bitten, sie anzulegen.

Hinweis: Die vorhandene Memory betrifft das **Email-Entwurf-Setup** (nicht dieses
Projekt) und verweist auf rechner-lokale Dinge (Script unter `~/.local/bin/`,
Skill unter `~/.claude/skills/`, Passwort im Keychain), die separat kopiert
werden müssten. Fürs Kundenportal ist das nicht nötig.

## 6. Claude Code starten

```bash
cd kundenportal-heimathafen
claude
```

## Arbeiten mit zwei Maschinen

Beide pushen auf dasselbe `origin/main`: vor dem Arbeiten `git pull`, nach jedem
Schritt committen + pushen. Bei parallelem Arbeiten Feature-Branches nutzen.
