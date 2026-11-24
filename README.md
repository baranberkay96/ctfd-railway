# Deploy and Host CTFd with Railway

CTFd is an open-source Capture The Flag platform for security competitions, training and classroom exercises. This community template runs CTFd 3.8.9 with MariaDB and Redis, finishes CTFd's setup wizard for you from Railway variables, and creates the administrator before the site goes online, so the setup page is never open on the internet.

## About Hosting CTFd

CTFd is a Python (Flask) web application. In production it needs a relational database for users, teams, challenges and submissions, a Redis cache for sessions, scoreboard caching and rate limits, and persistent storage for challenge files. This template runs the official CTFd image with Gunicorn (gevent workers), MariaDB 10.11 LTS with the character set and timeouts CTFd's own docker-compose uses, and Redis with a password. Uploaded challenge files live on a Railway volume. On a fresh instance CTFd normally shows a public `/setup` page where the first visitor becomes the administrator; here a start script runs database migrations and completes that setup from variables before the web server starts.

## Common Use Cases

- Running a CTF competition for a company, university, meetup or conference
- Security awareness and red/blue team training with jeopardy-style challenges
- Classroom exercises with automatic scoring and a live scoreboard
- Team hiring challenges and internal hackathons

## Dependencies for CTFd Hosting

- CTFd 3.8.9 (official image `ctfd/ctfd`, pinned by digest)
- MariaDB 10.11.19 LTS (official image)
- Redis 8.8.4 (official image)

### Deployment Dependencies

- CTFd documentation: https://docs.ctfd.io/
- Source code and releases: https://github.com/CTFd/CTFd
- Configuration reference: https://docs.ctfd.io/docs/deployment/configuration
- MariaDB: https://mariadb.org/

### Implementation Details

| Service | Role | Public |
|---|---|---|
| CTFd | Web application (Gunicorn, 2 gevent workers); volume `/var/uploads` for challenge files | HTTPS domain |
| MariaDB | Users, teams, challenges, flags, submissions and settings; volume | no |
| Redis | Cache, sessions and rate limits; volume | no |

**First login**

1. Wait until the CTFd service is healthy (`/healthcheck`). The first deploy builds a thin image and creates the database tables.
2. Copy `CTFD_ADMIN_NAME` (default `admin`) and `CTFD_ADMIN_PASSWORD` (generated) from the CTFd service's Variables.
3. Open the public domain, click Login and sign in. Admin Panel is at `/admin`.
4. Change the event name, dates, theme and e-mail settings in Admin Panel > Config, and set your own e-mail address in the admin's profile.

The first-boot setup uses `CTFD_NAME`, `CTFD_DESCRIPTION`, `CTFD_USER_MODE` (`users` or `teams`) and `CTFD_REGISTRATION` (`public` or `private`). After that, everything is managed in the Admin Panel. Challenge visibility starts as private (players must log in), and the scoreboard is public.

Invalid values never break the deploy: an unusable admin name or e-mail falls back to the default with a warning in the log. A password shorter than 8 characters still completes the setup, but the admin gets a random password nobody knows until you set a valid `CTFD_ADMIN_PASSWORD` and redeploy. Forgot the password? Set a new `CTFD_ADMIN_PASSWORD` and `CTFD_ADMIN_PASSWORD_RESET=true`, redeploy, then set it back to `false`.

**E-mail.** Configure e-mail in Admin Panel > Config > Email. CTFd supports SMTP and the Mailgun HTTP API; Railway allows outbound SMTP only on the Pro plan, so use Mailgun or another HTTP API on other plans.

**Custom domain.** Add it in the CTFd service's Settings > Networking. No CTFd variable needs to change; `REVERSE_PROXY=true` makes CTFd use the host and scheme Railway forwards.

**Scaling for an event.** Raise `WORKERS` (each gevent worker handles many concurrent players and needs about 150 MB) together with the service's CPU and memory, and raise `MARIADB_INNODB_BUFFER_POOL_SIZE` for large events. Keep one CTFd replica: uploaded files are on the service's volume.

**Backups.** Export the whole CTF (challenges, users, submissions and files) from Admin Panel > Config > Backup, and use Railway volume backups for MariaDB and the uploads volume.

**Resources and plans.** Measured on Railway (2026-11-24): CTFd about 0.3 GB of RAM at idle with 2 workers, MariaDB about 0.1 GB and Redis a few MB, so a small event costs roughly $4-7 a month at Railway's usage prices. Every plan works for small events; use Hobby or Pro for public competitions.

**Upgrading CTFd.** The version is pinned in `services/ctfd/Dockerfile` (tag and digest). Database migrations run automatically at start (`flask db upgrade`). Export a backup before a major upgrade and read the release notes.

**License.** CTFd is open-source software under the Apache-2.0 license. This is a community template, not affiliated with CTFd LLC.

### Why Deploy CTFd on Railway?

Railway runs CTFd, MariaDB and Redis in one project with a private network, an HTTPS domain, persistent volumes, logs and usage-based pricing, so you pay for a CTF only while it runs. This template gives you a production-style CTFd in a few minutes with the administrator already created and no setup page exposed to the internet.
