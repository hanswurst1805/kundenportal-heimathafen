# Deployment auf einem Linux-VPS (reines Podman, ohne compose)

Dieses Verzeichnis enthält alles, um das Kundenportal auf einem externen
Linux-Server mit **reinen `podman`-Kommandos** zu betreiben:

| Datei | Zweck |
|-------|-------|
| `kundenportal.sh` | Start-/Verwaltungsskript (build, up, down, restart, update, logs, migrate, seed, destroy, install-service) |
| `kundenportal.env.example` | Konfigurationsvorlage |

Der Stack besteht aus drei Containern in einem gemeinsamen Podman-Netzwerk
(DNS-Aliase `db`, `api`, `caddy`):

- **`<projekt>-db`** – PostgreSQL 16, persistentes Volume, nur intern erreichbar
- **`<projekt>-api`** – FastAPI/uvicorn; führt beim Start automatisch `alembic upgrade head` aus
- **`<projekt>-caddy`** – Caddy als Reverse-Proxy + Auslieferung des gebauten Frontends; terminiert HTTPS und veröffentlicht Port 80/443

Das Frontend nutzt relative API-Pfade (`/api/v1`, `/auth`), daher ist keine
Build-Zeit-Konfiguration der API-URL nötig.

---

## 1. Voraussetzungen auf dem VPS

- Linux mit **Podman ≥ 4.4** (für automatisches DNS im User-Netzwerk via netavark)
- `git`
- DNS-A/AAAA-Record der Domain (z. B. `heihaf.kiste.org`) zeigt auf den Server
- Ports **80** und **443** von außen erreichbar (für Let's-Encrypt + Betrieb)

Podman installieren (Beispiele):

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y podman git

# Fedora/RHEL/Alma/Rocky
sudo dnf install -y podman git
```

Prüfen: `podman --version`

---

## 2. Projekt holen und konfigurieren

```bash
sudo mkdir -p /opt/kundenportal && sudo chown "$USER" /opt/kundenportal
git clone git@github.com:hanswurst1805/kundenportal-heimathafen.git /opt/kundenportal
cd /opt/kundenportal

cp deploy/kundenportal.env.example deploy/kundenportal.env
# Werte eintragen – mindestens:
#   DOMAIN, POSTGRES_PASSWORD, JWT_SECRET, INITIAL_ADMIN_PASSWORD
nano deploy/kundenportal.env
```

Sichere Zufallswerte erzeugen:

```bash
openssl rand -hex 32   # für JWT_SECRET
openssl rand -hex 24   # für POSTGRES_PASSWORD / INITIAL_ADMIN_PASSWORD
```

---

## 3. Starten

```bash
./deploy/kundenportal.sh up
```

Beim ersten Aufruf werden Netzwerk, Volumes und beide Images (API + Caddy
inkl. Frontend-Build) erzeugt, dann db → api → caddy gestartet. Die
Migrationen laufen automatisch im API-Container.

Status / Logs:

```bash
./deploy/kundenportal.sh status
./deploy/kundenportal.sh logs api      # oder: db | caddy
```

Optional einmalig Demo-Daten anlegen (idempotent):

```bash
./deploy/kundenportal.sh seed
```

Danach Login als `admin` mit dem in `INITIAL_ADMIN_PASSWORD` gesetzten Passwort
(2FA-Einrichtung wird beim ersten Login erzwungen).

---

## 4. Autostart beim Boot (systemd)

Empfohlen für Produktivbetrieb (als root, damit Ports 80/443 ohne
Zusatzkonfiguration funktionieren):

```bash
sudo ./deploy/kundenportal.sh install-service
sudo systemctl daemon-reload
sudo systemctl enable --now kundenportal.service
```

Die Container laufen mit `--restart=always`; die systemd-Unit sorgt zusätzlich
für den Start nach einem Reboot.

---

## 5. Update / Redeploy

Nach `git pull` die Images neu bauen und Container ersetzen (Daten bleiben):

```bash
cd /opt/kundenportal
git pull
./deploy/kundenportal.sh update
```

---

## 6. Weitere Befehle

```bash
./deploy/kundenportal.sh down       # Container stoppen+entfernen (Volumes bleiben)
./deploy/kundenportal.sh restart    # down + up
./deploy/kundenportal.sh migrate    # Migrationen manuell nachziehen
./deploy/kundenportal.sh build      # nur Images neu bauen
./deploy/kundenportal.sh destroy    # ACHTUNG: löscht auch Volumes (alle Daten!)
```

Eine alternative Konfigurationsdatei lässt sich mit `--env-file <pfad>`
übergeben (so können mehrere Instanzen mit unterschiedlichem `PROJECT` auf
einem Host laufen).

---

## Hinweise / Troubleshooting

- **Rootless-Podman & Ports < 1024:** Standardmäßig dürfen unprivilegierte
  Nutzer keine Ports unter 1024 binden. Entweder als root betreiben (siehe
  systemd oben), oder
  `sudo sysctl net.ipv4.ip_unprivileged_port_start=80` setzen, oder in
  `kundenportal.env` höhere Ports verwenden (`HTTP_PORT=8080`, `HTTPS_PORT=8443`)
  und einen vorgelagerten Proxy/Portweiterleitung nutzen.
- **Erstes TLS-Zertifikat:** Caddy holt das Let's-Encrypt-Zertifikat erst, wenn
  die Domain öffentlich auf den Server zeigt und Port 80/443 erreichbar sind.
  Für einen Test ohne TLS `DOMAIN=:80` setzen.
- **Test ohne echte Domain:** `DOMAIN=:80`, dann ist die App über die
  Server-IP auf `HTTP_PORT` erreichbar.
- **Backups:** Das Datenbank-Volume heißt `<PROJECT>_pgdata`. Sicherung z. B. mit
  `podman exec <PROJECT>-db pg_dump -U <user> <db> > backup.sql`.
- **Rootless-Autostart ohne systemd-Unit:** alternativ
  `loginctl enable-linger <user>` + `systemctl --user enable podman-restart`.
