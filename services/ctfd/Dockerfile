# CTFd for Railway: the official image plus a start script that finishes CTFd's first-run
# setup from Railway variables before the web server starts (no open /setup page).
#
# Pinned by tag and digest. To upgrade, change both to a newer release:
# https://hub.docker.com/r/ctfd/ctfd/tags (release notes: https://github.com/CTFd/CTFd/releases)
FROM ctfd/ctfd:3.8.9@sha256:84aff1e50b6a6f931b5da90c6f5b7c623ba4583217a9b00e9d4c1b7c53b9739f

USER root
COPY --chmod=0755 railway-start.sh /opt/railway/railway-start
COPY --chmod=0644 railway_bootstrap.py /opt/railway/railway_bootstrap.py

RUN command -v setpriv gunicorn flask >/dev/null \
 && bash -n /opt/railway/railway-start \
 && python -m py_compile /opt/railway/railway_bootstrap.py

ENTRYPOINT ["/opt/railway/railway-start"]
