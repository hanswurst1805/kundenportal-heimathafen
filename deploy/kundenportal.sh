#!/usr/bin/env bash
#
# Kundenportal Heimathafen – Deployment mit reinem Podman (ohne podman-compose).
#
# Startet den kompletten Stack als drei Container in einem gemeinsamen
# Podman-Netzwerk (DNS-Aliase db / api / caddy):
#   - <projekt>-db     PostgreSQL 16 (persistentes Volume, nur intern)
#   - <projekt>-api    FastAPI/uvicorn (fuehrt beim Start die DB-Migrationen aus)
#   - <projekt>-caddy  Reverse-Proxy + statisches Frontend, veroeffentlicht 80/443
#
# Konfiguration kommt aus deploy/kundenportal.env (siehe *.env.example).
#
# Nutzung:
#   ./deploy/kundenportal.sh <befehl> [optionen]
#
# Befehle:
#   up                 Netzwerk/Volumes/Images sicherstellen und Container starten
#   down               Container stoppen und entfernen (Daten-Volumes bleiben)
#   restart            down + up
#   update             Container entfernen, Images neu bauen, neu starten (Redeploy)
#   build              API- und Caddy-Image (neu) bauen
#   status             Status der Container anzeigen
#   logs [svc]         Logs folgen (svc = db|api|caddy, Default: api)
#   migrate            alembic upgrade head im laufenden API-Container
#   seed               Demo-Daten anlegen (idempotent)
#   destroy            Container UND Volumes/Netzwerk entfernen (loescht alle Daten!)
#   install-service    systemd-Unit fuer Autostart beim Boot erzeugen
#
# Optionen:
#   --env-file <pfad>  Konfigurationsdatei (Default: deploy/kundenportal.env)
#   --build            bei `up` die Images vor dem Start (neu) bauen
#   -h | --help        diese Hilfe
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_ENV_FILE="${KUNDENPORTAL_ENV:-$SCRIPT_DIR/kundenportal.env}"

# Fixe DNS-Aliase – muessen zu Caddyfile (api:8000) und DATABASE_URL (db:5432) passen.
ALIAS_DB="db"
ALIAS_API="api"
ALIAS_CADDY="caddy"

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
log()  { printf '\033[1;34m[kundenportal]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[kundenportal]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[kundenportal]\033[0m %s\n' "$*" >&2; exit 1; }

usage() { awk 'NR>=2 && /^set -euo pipefail/{exit} NR>=2{sub(/^# ?/,""); print}' "$SCRIPT_PATH"; }

need_podman() { command -v podman >/dev/null 2>&1 || die "podman ist nicht installiert oder nicht im PATH."; }

load_env() {
  [ -f "$ENV_FILE" ] || die "Konfigurationsdatei nicht gefunden: $ENV_FILE
Kopiere deploy/kundenportal.env.example -> $ENV_FILE und trage Werte ein."
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a

  # Defaults fuer optionale Werte
  : "${PROJECT:=kundenportal}"
  : "${IMAGE_TAG:=latest}"
  : "${POSTGRES_IMAGE:=docker.io/postgres:16}"
  : "${POSTGRES_DB:=kundenportal}"
  : "${POSTGRES_USER:=kundenportal}"
  : "${JWT_EXPIRE_HOURS:=8}"
  : "${LOG_LEVEL:=INFO}"
  : "${SIGNATURE_PROVIDER:=stub}"
  : "${AVV_PROVIDER:=stub}"
  : "${TARGET_SYSTEM_PROVIDER:=stub}"
  : "${NOTIFICATION_PROVIDER:=stub}"
  : "${SEED_DEMO_DATA:=false}"
  : "${HTTP_PORT:=80}"
  : "${HTTPS_PORT:=443}"

  # Pflichtwerte pruefen
  : "${DOMAIN:?DOMAIN muss in $ENV_FILE gesetzt sein}"
  : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD muss in $ENV_FILE gesetzt sein}"
  : "${JWT_SECRET:?JWT_SECRET muss in $ENV_FILE gesetzt sein}"
  : "${INITIAL_ADMIN_PASSWORD:?INITIAL_ADMIN_PASSWORD muss in $ENV_FILE gesetzt sein}"

  # Abgeleitete Namen
  NETWORK="${PROJECT}-net"
  DB_NAME="${PROJECT}-db"
  API_NAME="${PROJECT}-api"
  CADDY_NAME="${PROJECT}-caddy"
  PGDATA_VOLUME="${PROJECT}_pgdata"
  CADDY_DATA_VOLUME="${PROJECT}_caddy_data"
  CADDY_CONFIG_VOLUME="${PROJECT}_caddy_config"
  API_IMAGE="${PROJECT}-api:${IMAGE_TAG}"
  CADDY_IMAGE="${PROJECT}-caddy:${IMAGE_TAG}"
  DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${ALIAS_DB}:5432/${POSTGRES_DB}"
}

container_exists()  { podman container exists "$1"; }
container_running() { [ "$(podman inspect -f '{{.State.Running}}' "$1" 2>/dev/null || echo false)" = "true" ]; }
image_exists()      { podman image exists "$1"; }

ensure_network() {
  if ! podman network exists "$NETWORK"; then
    log "Erstelle Netzwerk $NETWORK"
    podman network create "$NETWORK" >/dev/null
  fi
}

ensure_volumes() {
  for v in "$PGDATA_VOLUME" "$CADDY_DATA_VOLUME" "$CADDY_CONFIG_VOLUME"; do
    if ! podman volume exists "$v"; then
      log "Erstelle Volume $v"
      podman volume create "$v" >/dev/null
    fi
  done
}

build_images() {
  log "Baue API-Image $API_IMAGE"
  podman build -t "$API_IMAGE" -f "$REPO_ROOT/Dockerfile" "$REPO_ROOT"
  log "Baue Caddy-Image $CADDY_IMAGE (inkl. Frontend-Build)"
  podman build -t "$CADDY_IMAGE" -f "$REPO_ROOT/Dockerfile.caddy" "$REPO_ROOT"
}

ensure_images() {
  if ! image_exists "$API_IMAGE" || ! image_exists "$CADDY_IMAGE"; then
    log "Images fehlen – baue sie jetzt."
    build_images
  fi
}

wait_for_db() {
  log "Warte auf Datenbank-Bereitschaft..."
  for _ in $(seq 1 60); do
    if podman exec "$DB_NAME" pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
      log "Datenbank ist bereit."
      return 0
    fi
    sleep 1
  done
  die "Datenbank wurde nicht rechtzeitig bereit. Logs: podman logs $DB_NAME"
}

run_db() {
  log "Starte Datenbank-Container $DB_NAME"
  podman run -d \
    --name "$DB_NAME" \
    --network "$NETWORK" --network-alias "$ALIAS_DB" \
    --restart=always \
    --label "io.kundenportal.project=$PROJECT" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -v "$PGDATA_VOLUME":/var/lib/postgresql/data \
    --health-cmd "pg_isready -U $POSTGRES_USER" \
    --health-interval 5s --health-timeout 5s --health-retries 5 \
    "$POSTGRES_IMAGE" >/dev/null
}

run_api() {
  log "Starte API-Container $API_NAME (fuehrt Migrationen aus)"
  podman run -d \
    --name "$API_NAME" \
    --network "$NETWORK" --network-alias "$ALIAS_API" \
    --restart=always \
    --label "io.kundenportal.project=$PROJECT" \
    --entrypoint /app/scripts/entrypoint.sh \
    -e DATABASE_URL="$DATABASE_URL" \
    -e JWT_SECRET="$JWT_SECRET" \
    -e JWT_EXPIRE_HOURS="$JWT_EXPIRE_HOURS" \
    -e INITIAL_ADMIN_PASSWORD="$INITIAL_ADMIN_PASSWORD" \
    -e SIGNATURE_PROVIDER="$SIGNATURE_PROVIDER" \
    -e AVV_PROVIDER="$AVV_PROVIDER" \
    -e TARGET_SYSTEM_PROVIDER="$TARGET_SYSTEM_PROVIDER" \
    -e NOTIFICATION_PROVIDER="$NOTIFICATION_PROVIDER" \
    -e DOMAIN="$DOMAIN" \
    -e LOG_LEVEL="$LOG_LEVEL" \
    -e SEED_DEMO_DATA="$SEED_DEMO_DATA" \
    "$API_IMAGE" >/dev/null
}

run_caddy() {
  log "Starte Caddy-Container $CADDY_NAME (Ports ${HTTP_PORT}:80, ${HTTPS_PORT}:443)"
  podman run -d \
    --name "$CADDY_NAME" \
    --network "$NETWORK" --network-alias "$ALIAS_CADDY" \
    --restart=always \
    --label "io.kundenportal.project=$PROJECT" \
    -e DOMAIN="$DOMAIN" \
    -p "${HTTP_PORT}:80" \
    -p "${HTTPS_PORT}:443" \
    -v "$CADDY_DATA_VOLUME":/data \
    -v "$CADDY_CONFIG_VOLUME":/config \
    "$CADDY_IMAGE" >/dev/null
}

# Startet einen Service: vorhandenen (gestoppten) Container starten, sonst neu anlegen.
ensure_service() {
  local name="$1" runner="$2"
  if container_exists "$name"; then
    if container_running "$name"; then
      log "$name laeuft bereits."
    else
      log "Starte vorhandenen Container $name"
      podman start "$name" >/dev/null
    fi
  else
    "$runner"
  fi
}

remove_container() {
  local name="$1"
  if container_exists "$name"; then
    log "Entferne Container $name"
    podman rm -f "$name" >/dev/null
  fi
}

# ---------------------------------------------------------------------------
# Befehle
# ---------------------------------------------------------------------------
cmd_up() {
  ensure_network
  ensure_volumes
  if [ "${DO_BUILD:-false}" = "true" ]; then
    build_images
  else
    ensure_images
  fi
  ensure_service "$DB_NAME" run_db
  wait_for_db
  ensure_service "$API_NAME" run_api
  ensure_service "$CADDY_NAME" run_caddy
  log "Fertig. Erreichbar unter: $DOMAIN  (HTTP ${HTTP_PORT} / HTTPS ${HTTPS_PORT})"
  cmd_status
}

cmd_down() {
  remove_container "$CADDY_NAME"
  remove_container "$API_NAME"
  remove_container "$DB_NAME"
  log "Container entfernt. Daten-Volumes bleiben erhalten."
}

cmd_restart() { cmd_down; cmd_up; }

cmd_update() {
  remove_container "$CADDY_NAME"
  remove_container "$API_NAME"
  remove_container "$DB_NAME"
  build_images
  cmd_up
}

cmd_status() {
  podman ps -a --filter "label=io.kundenportal.project=$PROJECT" \
    --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
}

cmd_logs() {
  local svc="${1:-api}"
  case "$svc" in
    db)    podman logs -f "$DB_NAME" ;;
    api)   podman logs -f "$API_NAME" ;;
    caddy) podman logs -f "$CADDY_NAME" ;;
    *)     die "Unbekannter Service '$svc' (erlaubt: db|api|caddy)" ;;
  esac
}

cmd_migrate() {
  container_running "$API_NAME" || die "API-Container laeuft nicht."
  log "Fuehre Migrationen aus..."
  podman exec "$API_NAME" alembic upgrade head
}

cmd_seed() {
  container_running "$API_NAME" || die "API-Container laeuft nicht."
  log "Lege Demo-Daten an (idempotent)..."
  podman exec "$API_NAME" python scripts/seed_demo_data.py
}

cmd_destroy() {
  cmd_down
  for v in "$PGDATA_VOLUME" "$CADDY_DATA_VOLUME" "$CADDY_CONFIG_VOLUME"; do
    if podman volume exists "$v"; then
      log "Entferne Volume $v"
      podman volume rm "$v" >/dev/null
    fi
  done
  if podman network exists "$NETWORK"; then
    log "Entferne Netzwerk $NETWORK"
    podman network rm "$NETWORK" >/dev/null
  fi
  log "Vollstaendig entfernt."
}

cmd_install_service() {
  local unit="/etc/systemd/system/${PROJECT}.service"
  local tmp
  tmp="$(mktemp)"
  cat > "$tmp" <<UNIT
[Unit]
Description=Kundenportal Heimathafen (Podman)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$REPO_ROOT
ExecStart=$SCRIPT_PATH up --env-file $ENV_FILE
ExecStop=$SCRIPT_PATH down --env-file $ENV_FILE
TimeoutStartSec=900

[Install]
WantedBy=multi-user.target
UNIT
  if [ "$(id -u)" -eq 0 ]; then
    install -m 0644 "$tmp" "$unit"
    rm -f "$tmp"
    log "systemd-Unit geschrieben: $unit"
    log "Aktivieren mit:"
    echo "    systemctl daemon-reload"
    echo "    systemctl enable --now ${PROJECT}.service"
  else
    log "Keine root-Rechte – Unit-Vorlage liegt unter: $tmp"
    log "Als root installieren mit:"
    echo "    sudo install -m 0644 $tmp $unit"
    echo "    sudo systemctl daemon-reload && sudo systemctl enable --now ${PROJECT}.service"
  fi
}

# ---------------------------------------------------------------------------
# Argument-Parsing
# ---------------------------------------------------------------------------
COMMAND=""
ENV_FILE="$DEFAULT_ENV_FILE"
DO_BUILD="false"
EXTRA_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --env-file) ENV_FILE="${2:?--env-file benoetigt einen Pfad}"; shift 2 ;;
    --build) DO_BUILD="true"; shift ;;
    up|down|restart|update|build|status|logs|migrate|seed|destroy|install-service)
      COMMAND="$1"; shift ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

[ -n "$COMMAND" ] || { usage; exit 1; }

need_podman
load_env

case "$COMMAND" in
  up)              cmd_up ;;
  down)            cmd_down ;;
  restart)         cmd_restart ;;
  update)          cmd_update ;;
  build)           build_images ;;
  status)          cmd_status ;;
  logs)            cmd_logs "${EXTRA_ARGS[0]:-api}" ;;
  migrate)         cmd_migrate ;;
  seed)            cmd_seed ;;
  destroy)         cmd_destroy ;;
  install-service) cmd_install_service ;;
  *)               usage; exit 1 ;;
esac
