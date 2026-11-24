# CTFd 3.8 Capture The Flag: composer spec

Listing name: **CTFd 3.8 Capture The Flag**
Description (74 chars): CTF platform with MariaDB and Redis, admin pre-created, no open setup page
Category: Other. Icon: `https://cdn.jsdelivr.net/gh/CTFd/CTFd@3.8.9/CTFd/themes/core/static/img/logo.png`
Repository: `baranberkay96/ctfd-railway` (this folder is the repo root).

## Services

| Service | Source | Public | Volume | Healthcheck |
|---|---|---|---|---|
| CTFd | repo `/services/ctfd`: `FROM ctfd/ctfd:3.8.9@sha256:84af…739f` + `railway-start.sh` + `railway_bootstrap.py` | domain → 8000 | `/var/uploads` | `/healthcheck`, 900 s |
| MariaDB | image `mariadb:10.11.19@sha256:e5fe…c0d7`, start command with CTFd's flags (utf8mb4, `wait_timeout=28800`) | no | `/var/lib/mysql` | — |
| Redis | image `redis:8.8.4-alpine@sha256:1273…efb5`, password, `--save 60 1`, 256 MB LRU | no | `/data` | — |

Pinned 2026-11-24: CTFd 3.8.9 (2026-10-22), MariaDB 10.11 LTS as in CTFd's docker-compose.

## Boot sequence (CTFd)

1. As root: create/chown `/var/uploads` (Railway volume) for uid 1001, then re-exec as uid 1001 (`setpriv`).
2. Validate `PORT`, `WORKERS` (1-32, default 2), `WORKER_CLASS`; one worker if `SECRET_KEY` is empty.
3. `ping.py` waits for MariaDB (max 30 min), `flask db upgrade` retries every 15 s.
4. `railway_bootstrap.py`: if CTFd is not set up, it performs the `/setup` steps from `CTFD_*` variables (configs, visibility, admin, index page, `setup=True`); a password outside 8-128 characters gives the admin a random password and sets a lock config. If already set up: `CTFD_ADMIN_PASSWORD_RESET=true` or the lock config sets the admin password. A failure before setup is complete exits 1 and is retried; Gunicorn is never started with `/setup` open.
5. Gunicorn on `[::]:PORT` (IPv4 + IPv6), gevent workers.

## Improvements over market templates

Market (2026-11): `ctfd/ctfd:latest` with SQLite on a volume, no Redis, setup wizard open (≈160 active); a MariaDB + Redis variant with a third-party image (≈1 active); a repo-built MySQL + Redis variant (≈9 active).

- No public `/setup`: the first visitor can no longer become the administrator.
- MariaDB 10.11 LTS (as upstream) instead of SQLite; Redis with a password for cache and sessions; 2 gevent workers with a fixed `SECRET_KEY`.
- Official image pinned by tag + digest; uploads volume owned by CTFd's user instead of running as root (`RAILWAY_RUN_UID=0` in the market template).
- Deploy-form values never fail the deploy (8.29).

## Resources

Measured on Railway, test project, 2026-11-24 (CTFd 3.8.9, MariaDB 10.11.19, Redis 8.8.4):

| Service | Idle RAM | CPU idle |
|---|---|---|
| CTFd (2 workers) | 0.16-0.23 GB (0.28 GB peak) | ~0.01 vCPU |
| MariaDB (256 MB buffer pool) | 0.18 GB | ~0 vCPU |
| Redis | 0.03 GB | ~0 vCPU |

Estimate: ≈ 0.44 GB total → ≈ $5-8/month for a small event. Every plan works (each service is far below 1 GB).

Railway prices: RAM $10/GB-month, vCPU $20/vCPU-month, volume $0.15/GB-month.

## Verification checklist

1. All services SUCCESS; `/healthcheck` 200.
2. `/setup` redirects away (setup complete); log `[railway-setup] setup finished from variables`.
3. Login as admin with the generated password; `/admin` reachable; wrong password rejected.
4. Create a challenge with a flag and a file; register a player; submit the flag; scoreboard shows the solve; the file downloads.
5. `CTFD_ADMIN_PASSWORD=abc` + reset → warning, healthy, old password valid; valid password + reset → new password works.
6. Redeploy: data and files persist.

## Open questions

- CTFd plugins/themes from third parties are not included; add them by extending the Dockerfile.
