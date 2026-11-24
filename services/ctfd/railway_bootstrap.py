"""Finish CTFd's first-run setup from Railway variables, so /setup is never open on the internet.

Runs after `flask db upgrade` and before gunicorn starts. While CTFd is not set up, it does
what the /setup form does (CTFd 3.8 CTFd/views.py: setup()) with values from:

  CTFD_NAME, CTFD_DESCRIPTION, CTFD_USER_MODE (users|teams), CTFD_REGISTRATION (public|private),
  CTFD_ADMIN_NAME, CTFD_ADMIN_EMAIL, CTFD_ADMIN_PASSWORD

Values typed into the deploy form never stop the start (STANDARD 8.29): invalid ones fall back
to defaults with a warning; an unusable password (under 8 or over 128 characters) still
completes the setup but gives the admin a random password nobody knows, so the instance stays
closed until CTFD_ADMIN_PASSWORD is fixed (it is then applied on the next boot).

CTFD_ADMIN_PASSWORD_RESET=true sets the password of CTFD_ADMIN_NAME from CTFD_ADMIN_PASSWORD
(recovery); otherwise the admin account is managed in CTFd after the first boot.
"""
import os
import re
import secrets
import sys

LOCK_MARKER = "railway_admin_locked"


def log(message: str) -> None:
    print(f"[railway-setup] {message}", flush=True)


def env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def password_ok(password: str) -> bool:
    return 8 <= len(password) <= 128


def main() -> int:
    from CTFd import create_app
    from CTFd.cache import cache
    from CTFd.models import db
    from CTFd.utils import get_config

    app = create_app()
    with app.app_context(), app.test_request_context("/"):
        name = env("CTFD_ADMIN_NAME", "admin")
        email = env("CTFD_ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("CTFD_ADMIN_PASSWORD") or ""
        if not re.fullmatch(r"[^@\s][^\s]{0,127}", name) or "@" in name:
            log(f"WARNING: CTFD_ADMIN_NAME '{name}' is not a usable user name; using 'admin'.")
            name = "admin"
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            log("WARNING: CTFD_ADMIN_EMAIL is not an e-mail address; using admin@example.com.")
            email = "admin@example.com"

        cache.clear()
        if not get_config("setup"):
            setup(name, email, password)
        else:
            try:
                maintain(name, password)
            except Exception as err:  # the instance is set up: never block the start
                log(f"WARNING: admin maintenance failed: {type(err).__name__}: {str(err)[:300]}")
        db.session.close()
        cache.clear()
    return 0


def setup(name, email, password) -> None:
    from CTFd.constants.config import (
        AccountVisibilityTypes,
        ChallengeVisibilityTypes,
        ConfigTypes,
        RegistrationVisibilityTypes,
        ScoreVisibilityTypes,
    )
    from CTFd.constants.themes import DEFAULT_THEME
    from CTFd.models import Admins, Pages, Users, db
    from CTFd.utils import set_config
    from flask import url_for

    ctf_name = env("CTFD_NAME", "CTF")[:128]
    description = env("CTFD_DESCRIPTION", "")
    user_mode = env("CTFD_USER_MODE", "users").lower()
    if user_mode not in ("users", "teams"):
        log(f"WARNING: CTFD_USER_MODE '{user_mode}' is not users or teams; using users.")
        user_mode = "users"
    registration = env("CTFD_REGISTRATION", "public").lower()
    if registration not in ("public", "private"):
        log(f"WARNING: CTFD_REGISTRATION '{registration}' is not public or private; using public.")
        registration = "public"

    locked = not password_ok(password)
    if locked:
        password = secrets.token_urlsafe(32)

    # An account with the same name or e-mail would make the admin insert fail.
    existing = Users.query.filter((Users.name == name) | (Users.email == email)).first()
    if existing is not None:
        log("WARNING: a user with that name or e-mail already exists; it is promoted to admin.")
        existing.type = "admin"
        existing.password = password
        existing.hidden = True
        admin = existing
    else:
        admin = Admins(name=name, email=email, password=password, type="admin", hidden=True)

    set_config("ctf_name", ctf_name)
    set_config("ctf_description", description)
    set_config("user_mode", user_mode)
    set_config("ctf_theme", DEFAULT_THEME)
    set_config("start", None)
    set_config("end", None)
    set_config("freeze", None)
    set_config(ConfigTypes.CHALLENGE_VISIBILITY, ChallengeVisibilityTypes.PRIVATE)
    set_config(ConfigTypes.REGISTRATION_VISIBILITY, RegistrationVisibilityTypes(registration))
    set_config(ConfigTypes.SCORE_VISIBILITY, ScoreVisibilityTypes.PUBLIC)
    set_config(ConfigTypes.ACCOUNT_VISIBILITY, AccountVisibilityTypes.PUBLIC)
    set_config("verify_emails", None)
    set_config("social_shares", None)
    set_config("team_size", None)
    for key in ("mail_server", "mail_port", "mail_tls", "mail_ssl", "mail_username", "mail_password", "mail_useauth"):
        set_config(key, None)
    set_config(LOCK_MARKER, True if locked else None)

    banner = url_for("views.themes", path="img/logo.png")
    page = Pages(title=ctf_name, route="index", draft=False, content=(
        '<div class="row"><div class="col-md-6 offset-md-3">'
        f'<img class="w-100 mx-auto d-block" style="max-width: 500px;padding: 50px;padding-top: 14vh;" src="{banner}" />'
        f'<h3 class="text-center">{ctf_name}</h3><br>'
        '<h4 class="text-center"><a href="login">Log in</a> or <a href="register">register</a> to play.</h4>'
        "</div></div>"))

    db.session.add(admin)
    db.session.commit()
    if Pages.query.filter_by(route="index").first() is None:
        db.session.add(page)
        db.session.commit()
    set_config("setup", True)
    if locked:
        log(f"WARNING: CTFD_ADMIN_PASSWORD must have 8-128 characters. Setup is finished, but the admin '{name}' "
            "got a random password nobody knows. Set a valid CTFD_ADMIN_PASSWORD and redeploy to unlock it.")
    else:
        log(f"setup finished from variables: CTF '{ctf_name}', mode {user_mode}, admin '{name}'. /setup is closed.")


def maintain(name, password) -> None:
    from CTFd.models import Users, db
    from CTFd.utils import get_config, set_config

    reset = env("CTFD_ADMIN_PASSWORD_RESET", "false").lower() == "true"
    locked = bool(get_config(LOCK_MARKER))
    if not (reset or locked):
        log("CTFd is already set up; the admin account is managed in CTFd.")
        return
    if not password_ok(password):
        log("WARNING: CTFD_ADMIN_PASSWORD must have 8-128 characters; admin password unchanged"
            + (" (the admin is still locked)." if locked else "."))
        return
    user = Users.query.filter_by(name=name, type="admin").first()
    if user is None:
        user = Users.query.filter_by(type="admin").order_by(Users.id).first()
    if user is None:
        log("WARNING: no admin account found; password unchanged.")
        return
    user.password = password
    db.session.commit()
    set_config(LOCK_MARKER, None)
    log(f"password of admin '{user.name}' set from CTFD_ADMIN_PASSWORD. Set CTFD_ADMIN_PASSWORD_RESET back to false.")


if __name__ == "__main__":
    # A failure before the setup is complete exits 1: the start script retries and never
    # serves an instance whose /setup page is still open.
    try:
        sys.exit(main())
    except Exception as err:
        log(f"ERROR: setup from variables failed: {type(err).__name__}: {str(err)[:300]}")
        sys.exit(1)
