"""
welcome_email.py — GameRadar AI · Plan Rookie Welcome Email
============================================================

Renders a personalised HTML welcome email with Jinja2 and sends it via SMTP.
Designed to be called automatically when a new user registers for Plan Rookie
— either imported as a module or triggered from the CLI.

Module usage (integrate with your registration handler)
-------------------------------------------------------
    from welcome_email import send_welcome_email

    # On new user registration:
    ok = send_welcome_email(
        user_name   = "Faker",
        user_email  = "faker@t1.kr",
        region_plan = "Korea LCK",
    )

CLI usage
---------
    python welcome_email.py --name "Faker" --email "faker@t1.kr" --plan "Korea LCK"
    python welcome_email.py --name "Scout" --email "scout@tec.gg"  --dry-run
    python welcome_email.py --name "Test"  --email "me@test.com"   --html-only

SMTP configuration (environment variables or .env file)
-------------------------------------------------------
    SMTP_HOST       Mail server hostname   (default: smtp.gmail.com)
    SMTP_PORT       Port                   (default: 587 — STARTTLS)
    SMTP_USER       Sender login
    SMTP_PASSWORD   Sender password / app-password
    SMTP_FROM       Display name + address (default: SMTP_USER value)
    SMTP_SSL        "true" → SSL/port-465 mode (default: false → STARTTLS)

Template
--------
    templates/welcome_email.html  — Jinja2 HTML template
    Resolved relative to this script's directory.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import smtplib
import sys
import time
from datetime import datetime, timezone
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from loguru import logger

# ── Optional: python-dotenv ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Jinja2 ────────────────────────────────────────────────────────────────────
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_OK = True
except ImportError:
    JINJA2_OK = False
    logger.error("Jinja2 not installed.  Run: pip install jinja2")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = pathlib.Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATE_FILE = "welcome_email.html"
OUTPUT_DIR   = BASE_DIR / "reports"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — TEMPLATE CONTEXT
# ══════════════════════════════════════════════════════════════════════════════

# Default features shown in the "What happens next?" block
_DEFAULT_FEATURES = [
    {
        "icon":        "📅",
        "color":       "38bdf8",   # cyan
        "title":       "Your Weekly Radar",
        "description": "Every Monday at 08:00 UTC, you will receive a custom "
                       "Intelligence PDF Report directly in your inbox.",
    },
    {
        "icon":        "🌐",
        "color":       "a855f7",   # purple
        "title":       "The Data",
        "description": "We've already started scraping and translating live data "
                       "from Wanplus (China), Dak.gg (Korea), and The Esports Club "
                       "(India) — just for you.",
    },
    {
        "icon":        "🧠",
        "color":       "34d399",   # green
        "title":       "The GameRadar Score",
        "description": "Our scores are normalized. A '90' in Korea is compared "
                       "scientifically to an '85' in Vietnam. Trust the math.",
    },
]

# Default next-steps list
_DEFAULT_STEPS = [
    "Check your inbox every Monday at 08:00 UTC for your weekly Intelligence PDF Report.",
    "Open the attached Sample Report to learn how to read the metrics before your first delivery.",
    "Reply to this email to request a custom region or player deep-dive.",
    "Follow @GameRadarAI for real-time alerts and patch analysis.",
]

# Platform stats shown in the stats row
_DEFAULT_STATS = {
    "regions": "8+",
    "players": "500+",
    "reports": "4",
}


def _build_context(
    user_name:     str,
    user_email:    str,
    region_plan:   str = "",
    dashboard_url: str = "https://gameradar.ai/dashboard",
    features:      list[dict] | None = None,
    steps:         list[str]  | None = None,
    stats:         dict       | None = None,
) -> dict[str, Any]:
    """
    Assemble the Jinja2 template context for a given registrant.

    All values have sensible defaults so the only required fields are
    user_name and user_email.
    """
    from datetime import date, timedelta
    now   = datetime.now(timezone.utc)
    today = now.date()
    # Next Monday (same day counts as next week so delivery is always in the future)
    days_until_monday = (7 - today.weekday()) % 7 or 7
    next_mon = today + timedelta(days=days_until_monday)
    next_delivery = next_mon.strftime("%B %d, %Y") + " at 08:00 UTC"

    return {
        "user_name":      user_name.strip() or "Scout",
        "user_email":     user_email.strip(),
        "region_plan":    region_plan.strip(),
        "dashboard_url":  dashboard_url,
        "features":       features or _DEFAULT_FEATURES,
        # steps: list of (index, text) tuples for numbered rendering
        "steps":          list(enumerate((steps or _DEFAULT_STEPS), start=1)),
        "stats":          stats or _DEFAULT_STATS,
        "next_delivery":  next_delivery,
        "registered_at":  now.strftime("%b %d, %Y %H:%M UTC"),
        "year":           now.year,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — HTML RENDERER
# ══════════════════════════════════════════════════════════════════════════════

def render_welcome_email(
    user_name:     str,
    user_email:    str,
    region_plan:   str = "",
    *,
    dashboard_url: str = "https://gameradar.ai/dashboard",
    features:      list[dict] | None = None,
    steps:         list[str]  | None = None,
    stats:         dict       | None = None,
) -> str:
    """
    Render and return the welcome email as an HTML string.

    Parameters
    ----------
    user_name     : Recipient's display name.
    user_email    : Recipient's email address (shown in footer).
    region_plan   : Plan/region label, e.g. "Korea LCK".  Optional.
    dashboard_url : CTA button target URL.
    features      : Override the default "What's included" feature list.
    steps         : Override the default next-steps list.
    stats         : Override the default platform stats dict.

    Returns
    -------
    Rendered HTML string.

    Raises
    ------
    RuntimeError  : If Jinja2 is not installed or the template file is missing.
    """
    if not JINJA2_OK:
        raise RuntimeError("Jinja2 is not installed.  Run: pip install jinja2")

    template_path = TEMPLATE_DIR / TEMPLATE_FILE
    if not template_path.exists():
        raise RuntimeError(
            f"Template not found: {template_path}\n"
            f"  Ensure {TEMPLATE_FILE} exists in {TEMPLATE_DIR}"
        )

    env = Environment(
        loader     = FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape = select_autoescape(["html"]),
    )
    template = env.get_template(TEMPLATE_FILE)

    context = _build_context(
        user_name     = user_name,
        user_email    = user_email,
        region_plan   = region_plan,
        dashboard_url = dashboard_url,
        features      = features,
        steps         = steps,
        stats         = stats,
    )

    return template.render(**context)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SMTP HELPERS (reuses same env-var contract as delivery.py)
# ══════════════════════════════════════════════════════════════════════════════

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
    re.IGNORECASE,
)


def _sanitise_header(value: str) -> str:
    """Strip CR/LF to prevent email header injection (OWASP CWE-93)."""
    return re.sub(r"[\r\n]", "", value)


def _load_smtp() -> dict:
    user     = os.environ.get("SMTP_USER",     "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not user or not password:
        raise EnvironmentError(
            "SMTP credentials not set.\n"
            "  Export SMTP_USER and SMTP_PASSWORD before sending.\n"
            "  Gmail: use an App Password — "
            "https://myaccount.google.com/apppasswords"
        )
    return {
        "host":      os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port":      int(os.environ.get("SMTP_PORT", "587")),
        "user":      user,
        "password":  password,
        "from_addr": os.environ.get("SMTP_FROM", user).strip(),
        "use_ssl":   os.environ.get("SMTP_SSL", "false").lower() == "true",
    }


def _build_mime(
    to_email:    str,
    html_body:   str,
    from_addr:   str,
    region_plan: str,
    user_name:   str = "",
) -> MIMEMultipart:
    """Build a MIME multipart/alternative message with an HTML body."""
    safe_to     = _sanitise_header(to_email)
    safe_region = _sanitise_header(region_plan) if region_plan else "Plan Rookie"
    safe_from   = _sanitise_header(from_addr)
    safe_name   = _sanitise_header(user_name) if user_name else "Scout"

    subject = f"\u26a1 Welcome to the Future of Scouting, {safe_name}!"

    msg = MIMEMultipart("alternative")
    msg["From"]    = safe_from
    msg["To"]      = safe_to
    msg["Subject"] = subject

    # Plain-text fallback (brief, for spam-score improvement)
    plain = (
        f"Welcome to GameRadar AI — {safe_region}\n\n"
        f"Hello {safe_name},\n\n"
        "Welcome to GameRadar AI. You've just unlocked the most powerful, "
        "data-driven edge in the Asian esports market.\n\n"
        "Your Weekly Radar: Every Monday at 08:00 UTC, you will receive a "
        "custom Intelligence PDF Report in your inbox.\n\n"
        "Stop guessing. Start scouting with Neural Intelligence.\n\n"
        "Marcelo & The GameRadar AI Team\n"
        "Scouting Simplified. Talent Magnified.\n"
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def _smtp_send(msg: MIMEMultipart, to_email: str, smtp: dict) -> None:
    """
    Connect, authenticate and send.  Raises on failure (caller handles retry).
    """
    if smtp["use_ssl"]:
        conn = smtplib.SMTP_SSL(smtp["host"], smtp["port"], timeout=30)
    else:
        conn = smtplib.SMTP(smtp["host"], smtp["port"], timeout=30)
        conn.ehlo()
        conn.starttls()
        conn.ehlo()

    conn.login(smtp["user"], smtp["password"])
    conn.sendmail(smtp["from_addr"], [to_email], msg.as_bytes())
    conn.quit()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def send_welcome_email(
    user_name:    str,
    user_email:   str,
    region_plan:  str = "",
    *,
    max_retries:  int   = 3,
    retry_delay:  float = 2.0,
    dry_run:      bool  = False,
) -> bool:
    """
    Render and send the welcome email to a newly registered Rookie Plan user.

    Designed to be called from your registration handler immediately after
    a user confirms their account.  Safe to call concurrently from multiple
    threads — no shared state.

    Parameters
    ----------
    user_name    : Recipient's display name.
    user_email   : Recipient's email address.
    region_plan  : Plan/region label, e.g. "Korea LCK".  Optional.
    max_retries  : Number of SMTP send attempts before giving up (default: 3).
    retry_delay  : Base seconds for exponential backoff (default: 2.0).
    dry_run      : If True, render only — no SMTP connection made.

    Returns
    -------
    True if the email was sent (or would be sent in dry-run mode).
    False if all retry attempts failed.
    """
    if not _EMAIL_RE.match(user_email.strip()):
        logger.warning(f"Invalid email address '{user_email}' — skipping send")
        return False

    logger.info(f"Preparing welcome email for {user_email!r} (plan: {region_plan or 'Rookie'})")

    # Render HTML
    try:
        html_body = render_welcome_email(
            user_name   = user_name,
            user_email  = user_email,
            region_plan = region_plan,
        )
    except RuntimeError as exc:
        logger.error(f"Template render failed: {exc}")
        return False

    if dry_run:
        logger.info("[DRY-RUN] Email rendered — no SMTP call made")
        logger.info(f"[DRY-RUN]  To      : {user_email}")
        logger.info(f"[DRY-RUN]  Subject : \u26a1 Welcome to the Future of Scouting, {user_name}!")
        logger.info(f"[DRY-RUN]  Length  : {len(html_body):,} chars")
        return True

    # Load SMTP config
    try:
        smtp = _load_smtp()
    except EnvironmentError as exc:
        logger.error(str(exc))
        return False

    # Build MIME message
    msg = _build_mime(
        to_email    = user_email,
        html_body   = html_body,
        from_addr   = smtp["from_addr"],
        region_plan = region_plan,
        user_name   = user_name,
    )

    # Send with exponential-backoff retry
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            _smtp_send(msg, user_email, smtp)
            logger.success(
                f"Welcome email sent to {user_email!r}"
                f"{'  (attempt ' + str(attempt) + ')' if attempt > 1 else ''}"
            )
            return True

        except smtplib.SMTPRecipientsRefused as exc:
            # Permanent failure — no retry
            logger.error(f"Recipient refused by server: {exc.recipients}")
            return False

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed — check SMTP_USER / SMTP_PASSWORD."
            )
            return False

        except (smtplib.SMTPException, OSError) as exc:
            last_error = str(exc)
            wait = retry_delay * (2 ** (attempt - 1))
            if attempt < max_retries:
                logger.warning(
                    f"SMTP error (attempt {attempt}/{max_retries}): {exc} "
                    f"— retrying in {wait:.0f}s"
                )
                time.sleep(wait)
            else:
                logger.error(
                    f"Failed to send welcome email to {user_email!r} "
                    f"after {max_retries} attempts: {last_error}"
                )

    return False


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> "
            "| <level>{level:<8}</level> "
            "| <cyan>{function}</cyan> "
            "| {message}"
        ),
        colorize=True,
        level="DEBUG",
    )

    parser = argparse.ArgumentParser(
        description="GameRadar AI — Plan Rookie Welcome Email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python welcome_email.py --name Faker --email faker@t1.kr --plan 'Korea LCK'\n"
            "  python welcome_email.py --name Scout --email scout@tec.gg --dry-run\n"
            "  python welcome_email.py --name Test  --email me@test.com  --html-only\n"
            "\n"
            "SMTP env vars required (unless --dry-run / --html-only):\n"
            "  SMTP_USER      sender login\n"
            "  SMTP_PASSWORD  app-password\n"
        ),
    )

    parser.add_argument("--name",  "-n", required=True, help="Recipient display name")
    parser.add_argument("--email", "-e", required=True, help="Recipient email address")
    parser.add_argument("--plan",  "-p", default="",   help="Region/plan label, e.g. 'Korea LCK'")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the email and log what would be sent — no SMTP calls",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Write the rendered HTML to reports/ and open in browser, do not send",
    )

    args = parser.parse_args()

    if args.html_only:
        # Render and save for inspection
        try:
            html = render_welcome_email(
                user_name   = args.name,
                user_email  = args.email,
                region_plan = args.plan,
            )
        except RuntimeError as exc:
            logger.error(str(exc))
            sys.exit(1)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "welcome_preview.html"
        out_path.write_text(html, encoding="utf-8")
        logger.success(f"HTML preview written: {out_path}")

        # Attempt to open in browser (non-fatal)
        try:
            import subprocess, platform
            if platform.system() == "Windows":
                import os; os.startfile(str(out_path))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(out_path)], check=False)
            else:
                subprocess.run(["xdg-open", str(out_path)], check=False)
        except Exception:
            pass

        sys.exit(0)

    ok = send_welcome_email(
        user_name   = args.name,
        user_email  = args.email,
        region_plan = args.plan,
        dry_run     = args.dry_run,
    )
    sys.exit(0 if ok else 1)
