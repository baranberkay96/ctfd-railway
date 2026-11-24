# Notice

## Upstream software

This repository contains Railway configuration and small start/setup scripts only. CTFd, MariaDB and Redis are pulled from their official container images; they are not stored in this repository.

| Software | License | Source (publisher) |
|---|---|---|
| CTFd 3.8.9 | Apache-2.0 | `ctfd/ctfd:3.8.9@sha256:84aff1e50b6a6f931b5da90c6f5b7c623ba4583217a9b00e9d4c1b7c53b9739f` (CTFd) |
| MariaDB 10.11.19 | GPL-2.0 | `mariadb:10.11.19@sha256:e5fe75b2b9de0eb9f6f9a4d9c97272fb3a7480e389ccd487a786bab2a12cc0d7` (Docker Official Image) |
| Redis 8.8.4 | RSALv2 / SSPLv1 / AGPLv3 (Redis 8 tri-license) | `redis:8.8.4-alpine@sha256:1273af45b299d2b8b60d0e400d90aa6c2c5b1794f01d6a7ca60ff3ba6e65efb5` (Docker Official Image) |

CTFd source for the pinned release: https://github.com/CTFd/CTFd/tree/3.8.9 (LICENSE: Apache-2.0).

## Verified against

| What | Upstream file | Ref | Checked |
|---|---|---|---|
| Latest release | GitHub releases (`3.8.9`, 2026-10-22) | 3.8.9 | 2026-11-24 |
| Compose stack (MariaDB 10.11 flags, Redis, `UPLOAD_FOLDER`, `REVERSE_PROXY`, `WORKERS`) | `docker-compose.yml` | 3.8.9 | 2026-11-24 |
| Entrypoint (`ping.py`, `flask db upgrade`, Gunicorn flags) and image user (uid 1001) | `docker-entrypoint.sh`, `Dockerfile` | 3.8.9 | 2026-11-24 |
| First-run setup (configs, admin, index page) | `CTFd/views.py` `setup()` | 3.8.9 | 2026-11-24 |
| Health endpoint `/healthcheck` | `CTFd/views.py` | 3.8.9 | 2026-11-24 |
| Configuration keys | `CTFd/config.ini` | 3.8.9 | 2026-11-24 |

## Adapted code

| Our file | Source | Changes |
|---|---|---|
| `services/ctfd/railway_bootstrap.py` | Follows the steps of CTFd's `setup()` view (Apache-2.0, CTFd LLC) | Reads values from environment variables, validates them, never prints secrets; recovery of the admin password |
| `services/ctfd/railway-start.sh` | Follows CTFd's `docker-entrypoint.sh` (Apache-2.0) | Volume ownership, value validation, setup before Gunicorn, IPv4+IPv6 bind |

## Trademarks

"CTFd" is a trademark of CTFd LLC; "MariaDB", "Redis" and "Railway" belong to their respective owners. This is a community template and is not affiliated with or endorsed by them.
