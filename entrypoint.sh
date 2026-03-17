#!/bin/sh
# Ensure /data and the DB file exist. Run the app as root so it can always write
# (bind mounts often end up root-owned; chown may not take effect on some hosts).
# To run as a specific user, pre-create the data dir on the host and chown it to PUID:PGID.
set -e
mkdir -p /data
if [ ! -f /data/renfe_tracker.db ]; then
  touch /data/renfe_tracker.db
fi
# Optional: chown so if we later run as PUID (see below) the dir is ready
if [ -n "${PUID}" ] && [ -n "${PGID}" ] && [ "${PUID}" -eq "${PUID}" ] 2>/dev/null && [ "${PGID}" -eq "${PGID}" ] 2>/dev/null; then
  chown -R "${PUID}:${PGID}" /data 2>/dev/null || true
  chown -R "${PUID}:${PGID}" /app 2>/dev/null || true
fi
# Run app as root so it can open/write the DB on any volume (avoids "unable to open database file")
exec "$@"
