#!/bin/bash
# CTFd on Railway. Runs as root only to prepare the uploads volume, then as the image's
# ctfd user (uid 1001):
#   1. wait for MariaDB (CTFd's ping.py), 2. flask db upgrade,
#   3. finish the first-run setup from variables (railway_bootstrap.py) so /setup is never
#      open on the internet, 4. gunicorn on [::]:PORT (IPv4 and IPv6).
set -uo pipefail

log() { printf '[railway-start] %s\n' "$*"; }

if [ "$(id -u)" = 0 ]; then
  UPLOAD_FOLDER="${UPLOAD_FOLDER:-/var/uploads}"
  mkdir -p "${UPLOAD_FOLDER}" /var/log/CTFd
  rm -rf "${UPLOAD_FOLDER}/lost+found"
  chown -R 1001:1001 "${UPLOAD_FOLDER}" /var/log/CTFd
  exec setpriv --reuid=1001 --regid=1001 --clear-groups "$0" "$@"
fi

cd /opt/CTFd || exit 1
export HOME=/opt/CTFd
# railway_bootstrap.py lives in /opt/railway; CTFd must be importable from there.
export PYTHONPATH="/opt/CTFd${PYTHONPATH:+:${PYTHONPATH}}"

PORT="${PORT:-8000}"
[[ "${PORT}" =~ ^[0-9]{2,5}$ ]] || { log "WARNING: PORT='${PORT}' is not a port; using 8000."; PORT=8000; }
WORKERS="${WORKERS:-2}"
[[ "${WORKERS}" =~ ^[0-9]{1,2}$ ]] && [ "${WORKERS}" -ge 1 ] && [ "${WORKERS}" -le 32 ] \
  || { log "WARNING: WORKERS='${WORKERS}' is not 1-32; using 2."; WORKERS=2; }
if [ -z "${SECRET_KEY:-}" ] && [ "${WORKERS}" -gt 1 ]; then
  log "WARNING: SECRET_KEY is empty; CTFd needs it for more than one worker. Using 1 worker."
  WORKERS=1
fi
WORKER_CLASS="${WORKER_CLASS:-gevent}"
case "${WORKER_CLASS}" in gevent|sync|gthread) ;; *) log "WARNING: WORKER_CLASS='${WORKER_CLASS}' unsupported; using gevent."; WORKER_CLASS=gevent ;; esac

log "waiting for the database"
timeout 1800 python ping.py >/dev/null 2>&1 || log "WARNING: database not reachable after 30 minutes; trying anyway."

until flask db upgrade; do
  log "database migration failed; retrying in 15 s"
  sleep 15
done

# Never serve CTFd before its setup is complete: /setup would let anyone create the admin.
until python /opt/railway/railway_bootstrap.py; do
  log "setup from variables failed; retrying in 15 s (CTFd is not served until it succeeds)"
  sleep 15
done

log "starting CTFd on port ${PORT} with ${WORKERS} ${WORKER_CLASS} worker(s)"
exec gunicorn 'CTFd:create_app()' \
  --bind "[::]:${PORT}" \
  --workers "${WORKERS}" \
  --worker-tmp-dir /dev/shm \
  --worker-class "${WORKER_CLASS}" \
  --access-logfile "${ACCESS_LOG:--}" \
  --error-logfile "${ERROR_LOG:--}"
