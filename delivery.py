"""
delivery.py — GameRadar AI · Automated Weekly Report Delivery System
=====================================================================

Generates a personalised PDF Rookie Report for each unique region found in
subscribers.csv, then sends it via SMTP to every subscriber mapped to that
region.  A timestamped delivery log (CSV) is written to reports/ after every
run — both for successes and failures.

Usage
-----
    python delivery.py                       # full delivery
    python delivery.py --dry-run             # validate only, no SMTP calls
    python delivery.py --region "Korea LCK"  # deliver one region only
    python delivery.py --csv path/to/subs.csv

SMTP configuration (environment variables or .env file)
--------------------------------------------------------
    SMTP_HOST       Mail server hostname            (default: smtp.gmail.com)
    SMTP_PORT       587 = STARTTLS / 465 = SSL      (default: 587)
    SMTP_USER       Sender account username
    SMTP_PASSWORD   Sender account password / app-password
    SMTP_FROM       Display name + address          (default: SMTP_USER value)
    SMTP_SSL        "true" to force SSL wrapper     (default: false → STARTTLS)

Subscribers CSV
---------------
    email,region_plan
    analyst@esports.com,Korea LCK
    scout@gaming.io,India
    talent@agency.com,Asia Pacific

Requirements
------------
    pip install python-dotenv   # optional — loads .env automatically
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import re
import smtplib
import sys
import textwrap
import time
from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NamedTuple

from loguru import logger

# ── Optional: python-dotenv (loads .env file if present) ──────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env support is optional; env vars can be set directly

# ── PDF generator (same package) ──────────────────────────────────────────────
try:
    import generate_rookie_report as _grr
    PDF_GEN_OK = True
except ImportError:
    PDF_GEN_OK = False
    logger.error(
        "generate_rookie_report.py not found in the same directory.\n"
        "  Make sure delivery.py is run from d:\\gameradar\\gameradar"
    )

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = pathlib.Path(__file__).parent
REPORTS_DIR   = BASE_DIR / "reports"
DEFAULT_CSV   = BASE_DIR / "subscribers.csv"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — SMTP CONFIGURATION (from environment variables only)
# ══════════════════════════════════════════════════════════════════════════════

class SmtpConfig(NamedTuple):
    host:     str
    port:     int
    user:     str
    password: str
    from_addr: str
    use_ssl:  bool  # True → SSL wrapper (port 465); False → STARTTLS (port 587)


def _load_smtp_config() -> SmtpConfig:
    """
    Load SMTP credentials exclusively from environment variables.
    Raises ValueError (with instructions) if required variables are missing.
    """
    user     = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()

    if not user or not password:
        raise ValueError(
            "SMTP credentials not configured.\n"
            "  Set environment variables before running:\n"
            "    SMTP_USER=your@email.com\n"
            "    SMTP_PASSWORD=your-app-password\n"
            "  Or create a .env file in the project root with those keys.\n"
            "  For Gmail: generate an App Password at "
            "https://myaccount.google.com/apppasswords"
        )

    host     = os.environ.get("SMTP_HOST",     "smtp.gmail.com").strip()
    port     = int(os.environ.get("SMTP_PORT", "587"))
    from_addr = os.environ.get("SMTP_FROM",   user).strip()
    use_ssl  = os.environ.get("SMTP_SSL",     "false").lower() == "true"

    return SmtpConfig(
        host=host, port=port, user=user,
        password=password, from_addr=from_addr, use_ssl=use_ssl,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — REGION CONFIG
# ══════════════════════════════════════════════════════════════════════════════

# Maps region_plan values (case-insensitive) to report generator parameters.
# Add new regions here to expand coverage without touching the rest of the script.
REGION_CONFIG: dict[str, dict] = {
    "korea lck":     {"label": "Korea LCK",     "slug": "korea_lck",     "top_n": 10},
    "korea":         {"label": "Korea LCK",     "slug": "korea_lck",     "top_n": 10},
    "india":         {"label": "India",          "slug": "india",         "top_n": 10},
    "india tec":     {"label": "India",          "slug": "india",         "top_n": 10},
    "china lpl":     {"label": "China LPL",      "slug": "china_lpl",     "top_n": 10},
    "china":         {"label": "China LPL",      "slug": "china_lpl",     "top_n": 10},
    "lpl":           {"label": "China LPL",      "slug": "china_lpl",     "top_n": 10},
    "asia pacific":  {"label": "Asia Pacific",   "slug": "asia_pacific",  "top_n": 10},
    "asia":          {"label": "Asia Pacific",   "slug": "asia_pacific",  "top_n": 10},
    "japan ljl":     {"label": "Japan LJL",      "slug": "japan_ljl",     "top_n": 10},
    "japan":         {"label": "Japan LJL",      "slug": "japan_ljl",     "top_n": 10},
    "vietnam vcs":   {"label": "Vietnam VCS",    "slug": "vietnam_vcs",   "top_n": 10},
    "vietnam":       {"label": "Vietnam VCS",    "slug": "vietnam_vcs",   "top_n": 10},
}

_FALLBACK_CONFIG = {"label": "Global",  "slug": "global",  "top_n": 10}


def _region_cfg(region_plan: str) -> dict:
    """Return the config dict for a region_plan string (case-insensitive)."""
    return REGION_CONFIG.get(region_plan.lower().strip(), _FALLBACK_CONFIG)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SUBSCRIBER LOADING & VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
    re.IGNORECASE,
)


class Subscriber(NamedTuple):
    email:       str
    region_plan: str


def _validate_email(email: str) -> bool:
    """Return True if email looks syntactically valid (RFC 5322 simplified)."""
    return bool(_EMAIL_RE.match(email.strip()))


def _sanitise_header(value: str) -> str:
    """
    Strip newline characters from a string to prevent email header injection.
    OWASP: Email Header Injection — CWE-93.
    """
    return re.sub(r"[\r\n]", "", value)


def load_subscribers(csv_path: pathlib.Path) -> list[Subscriber]:
    """
    Parse subscribers.csv and return validated Subscriber records.

    Expected columns: email, region_plan  (header row required).
    Rows with invalid email format are skipped and logged as warnings.
    """
    if not csv_path.exists():
        logger.error(
            f"Subscriber file not found: {csv_path}\n"
            f"  Create it with columns:  email,region_plan\n"
            f"  Example:  analyst@esports.com,Korea LCK"
        )
        sys.exit(1)

    subscribers: list[Subscriber] = []
    skipped = 0

    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)

        # Normalise column names (strip whitespace, lowercase)
        if reader.fieldnames is None:
            logger.error("subscribers.csv is empty or has no header row.")
            sys.exit(1)

        required = {"email", "region_plan"}
        found = {c.strip().lower() for c in reader.fieldnames}
        if not required.issubset(found):
            logger.error(
                f"subscribers.csv must have columns: {required}. "
                f"Found: {reader.fieldnames}"
            )
            sys.exit(1)

        for i, row in enumerate(reader, start=2):  # row 1 = header
            email       = row.get("email", "").strip()
            region_plan = row.get("region_plan", "").strip()

            if not email:
                logger.warning(f"Row {i}: empty email — skipped")
                skipped += 1
                continue

            if not _validate_email(email):
                logger.warning(f"Row {i}: invalid email '{email}' — skipped")
                skipped += 1
                continue

            # ── Skip inactive subscribers (churned / cancelled) ───────────────
            status = row.get("status", "Active").strip()
            if status.lower() == "inactive":
                logger.debug(
                    f"Row {i}: {email} is Inactive — excluded from delivery"
                )
                skipped += 1
                continue

            if not region_plan:
                logger.warning(
                    f"Row {i}: email '{email}' has no region_plan — "
                    f"defaulting to 'Global'"
                )
                region_plan = "Global"

            subscribers.append(Subscriber(email=email, region_plan=region_plan))

    logger.info(
        f"Loaded {len(subscribers)} valid subscriber(s) "
        f"({skipped} skipped) from {csv_path.name}"
    )
    return subscribers


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — PDF GENERATION (per region, cached)
# ══════════════════════════════════════════════════════════════════════════════

def _pdf_filename(slug: str, report_month: str) -> str:
    """Return a safe PDF filename: <Slug>_Report_YYYY-MM.pdf"""
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    month_tag = datetime.now().strftime("%Y-%m")
    return f"{safe_slug.title().replace('_', '')}_Report_{month_tag}.pdf"


def generate_region_pdfs(
    subscribers: list[Subscriber],
    report_month: str,
    *,
    dry_run: bool = False,
    filter_region: str | None = None,
) -> dict[str, pathlib.Path | None]:
    """
    Generate one PDF per unique region found in the subscriber list.
    Returns a mapping of region_plan → pdf_path (None if generation failed).
    Uses WeasyPrint via generate_rookie_report.generate().
    """
    unique_regions = {s.region_plan for s in subscribers}
    if filter_region:
        unique_regions = {r for r in unique_regions if r.lower() == filter_region.lower()}

    region_pdf: dict[str, pathlib.Path | None] = {}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for region_plan in sorted(unique_regions):
        cfg       = _region_cfg(region_plan)
        pdf_name  = _pdf_filename(cfg["slug"], report_month)
        pdf_path  = REPORTS_DIR / pdf_name

        if dry_run:
            logger.info(f"[DRY-RUN] Would generate: {pdf_path}")
            region_pdf[region_plan] = pdf_path
            continue

        if pdf_path.exists():
            logger.info(f"Reusing cached PDF: {pdf_path.name}")
            region_pdf[region_plan] = pdf_path
            continue

        if not PDF_GEN_OK:
            logger.error("generate_rookie_report unavailable — cannot generate PDFs.")
            region_pdf[region_plan] = None
            continue

        logger.info(f"Generating report for region: {cfg['label']} → {pdf_path.name}")
        try:
            _grr.generate(
                output_path  = pdf_path,
                region       = cfg["label"],
                report_month = report_month,
                data_source  = "master",
                top_n        = cfg["top_n"],
                auto_open    = False,
                html_only    = False,
            )
            region_pdf[region_plan] = pdf_path if pdf_path.exists() else None
        except SystemExit as exc:
            logger.error(
                f"Report generation failed for '{region_plan}' "
                f"(SystemExit {exc.code}) — skipping region"
            )
            region_pdf[region_plan] = None
        except Exception as exc:
            logger.error(
                f"Unexpected error generating report for '{region_plan}': {exc}"
            )
            region_pdf[region_plan] = None

    return region_pdf


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — EMAIL BUILDER
# ══════════════════════════════════════════════════════════════════════════════

_HTML_BODY_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#060c16;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#060c16;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#0c1524;border:1px solid #1a2d4d;border-radius:12px;overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#060c16 0%,#0d1f3c 100%);
                        padding:28px 36px;border-bottom:2px solid #00d4ff;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:22px;font-weight:700;color:#e4eeff;
                                 letter-spacing:1px;">
                      GAME<span style="color:#00d4ff;">RADAR</span>
                      <span style="color:#6e88b8;font-size:14px;font-weight:400;">
                        &nbsp;AI
                      </span>
                    </span>
                    <div style="color:#6e88b8;font-size:11px;letter-spacing:2px;
                                margin-top:4px;">
                      SCOUTING INTELLIGENCE PLATFORM
                    </div>
                  </td>
                  <td align="right">
                    <span style="background:#00d4ff22;color:#00d4ff;
                                 border:1px solid #00d4ff44;border-radius:20px;
                                 padding:4px 14px;font-size:11px;font-weight:600;
                                 letter-spacing:1px;">
                      WEEKLY INSIGHTS
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px 36px;">
              <p style="color:#6e88b8;font-size:13px;margin:0 0 20px;">
                Your exclusive report is ready
              </p>
              <h1 style="color:#e4eeff;font-size:26px;font-weight:700;margin:0 0 8px;
                          line-height:1.2;">
                {region} Rookie Report
              </h1>
              <p style="color:#00d4ff;font-size:14px;font-weight:600;
                         margin:0 0 28px;letter-spacing:0.5px;">
                {report_month} Edition
              </p>

              <p style="color:#9ab0d0;font-size:14px;line-height:1.7;margin:0 0 16px;">
                Your personalised <strong style="color:#e4eeff;">GameRadar AI</strong>
                scouting report for <strong style="color:#00d4ff;">{region}</strong>
                is attached to this email.
              </p>
              <p style="color:#9ab0d0;font-size:14px;line-height:1.7;margin:0 0 28px;">
                Inside you will find:
              </p>

              <!-- Feature list -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                <tr>
                  <td width="24" valign="top" style="color:#00d4ff;font-size:18px;
                                                      padding-top:2px;">▸</td>
                  <td style="color:#9ab0d0;font-size:14px;line-height:1.6;
                              padding-bottom:10px;">
                    <strong style="color:#e4eeff;">Regional Top 10 Rankings</strong>
                    — scored by GameRadar AI (KDA · Win Rate · Match Frequency)
                  </td>
                </tr>
                <tr>
                  <td width="24" valign="top" style="color:#ffd700;font-size:18px;
                                                      padding-top:2px;">▸</td>
                  <td style="color:#9ab0d0;font-size:14px;line-height:1.6;
                              padding-bottom:10px;">
                    <strong style="color:#e4eeff;">Rising Stars</strong>
                    — three breakout players to watch this week
                  </td>
                </tr>
                <tr>
                  <td width="24" valign="top" style="color:#a855f7;font-size:18px;
                                                      padding-top:2px;">▸</td>
                  <td style="color:#9ab0d0;font-size:14px;line-height:1.6;">
                    <strong style="color:#e4eeff;">Market Trends</strong>
                    — translated intelligence from local forums (Wanplus · TEC)
                  </td>
                </tr>
              </table>

              <!-- CTA area -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#080f1e;border:1px solid #1a2d4d;
                            border-radius:8px;padding:0;margin-bottom:28px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="color:#6e88b8;font-size:12px;margin:0 0 6px;
                               letter-spacing:1px;text-transform:uppercase;">
                      Report generated
                    </p>
                    <p style="color:#e4eeff;font-size:15px;font-weight:600;margin:0;">
                      {report_date} &nbsp;&middot;&nbsp;
                      <span style="color:#00d4ff;">{region} Edition</span>
                    </p>
                  </td>
                </tr>
              </table>

              <p style="color:#9ab0d0;font-size:13px;line-height:1.6;margin:0;">
                Open the attached PDF for the full interactive report.
                Best viewed in Adobe Acrobat or any modern PDF reader.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 36px;border-top:1px solid #1a2d4d;
                        background:#080f1e;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="color:#3e5478;font-size:11px;line-height:1.6;">
                    GameRadar AI &copy; {year} &nbsp;|&nbsp;
                    Scouting Intelligence Platform<br>
                    You are receiving this report as a GameRadar subscriber.<br>
                    <a href="https://gameradar.ai/unsubscribe?email={{email}}&amp;region={{region_slug}}"
                       style="color:#3e5478;">Manage or cancel your subscription</a>
                  </td>
                  <td align="right" style="color:#3e5478;font-size:11px;">
                    {region_plan_display}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _build_email(
    to_email:     str,
    region:       str,
    region_plan:  str,
    pdf_path:     pathlib.Path,
    from_addr:    str,
    report_month: str,
) -> MIMEMultipart:
    """
    Construct a MIME multipart email with an HTML body and the PDF attached.
    All user-supplied strings are sanitised to prevent header injection.
    """
    safe_to      = _sanitise_header(to_email)
    safe_region  = _sanitise_header(region)
    safe_from    = _sanitise_header(from_addr)
    report_date  = datetime.now(timezone.utc).strftime("%B %d, %Y")

    msg = MIMEMultipart("mixed")
    msg["From"]    = safe_from
    msg["To"]      = safe_to
    msg["Subject"] = f"Your GameRadar AI Weekly Insights - {safe_region}"

    # HTML body
    html_body = _HTML_BODY_TEMPLATE.format(
        region              = safe_region,
        region_plan_display = _sanitise_header(region_plan),
        report_month        = _sanitise_header(report_month),
        report_date         = report_date,
        year                = datetime.now().year,
    )
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # PDF attachment
    with pdf_path.open("rb") as fh:
        part = MIMEBase("application", "pdf")
        part.set_payload(fh.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        "attachment",
        filename=pdf_path.name,
    )
    msg.attach(part)

    return msg


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — SMTP SENDER WITH RETRY
# ══════════════════════════════════════════════════════════════════════════════

_MAX_RETRIES    = 3
_RETRY_BASE_SEC = 2.0   # exponential: 2s, 4s, 8s


def _send_one(
    msg:     MIMEMultipart,
    to:      str,
    config:  SmtpConfig,
    *,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """
    Attempt to send a single email, with up to _MAX_RETRIES retries.
    Returns (success: bool, error_message: str).
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Would send '{msg['Subject']}' → {to}")
        return True, ""

    last_error = ""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if config.use_ssl:
                conn = smtplib.SMTP_SSL(config.host, config.port, timeout=30)
            else:
                conn = smtplib.SMTP(config.host, config.port, timeout=30)
                conn.ehlo()
                conn.starttls()
                conn.ehlo()

            conn.login(config.user, config.password)
            conn.sendmail(config.from_addr, [to], msg.as_bytes())
            conn.quit()
            return True, ""

        except smtplib.SMTPRecipientsRefused as exc:
            # Permanent failure — no point retrying
            last_error = f"Recipient refused: {exc.recipients}"
            logger.warning(f"Permanent SMTP failure for {to}: {last_error}")
            return False, last_error

        except smtplib.SMTPAuthenticationError as exc:
            # Auth error affects all sends — abort early
            last_error = f"SMTP authentication failed: {exc}"
            logger.error(last_error)
            raise  # propagate so the outer loop can abort

        except (smtplib.SMTPException, OSError) as exc:
            last_error = str(exc)
            wait = _RETRY_BASE_SEC * (2 ** (attempt - 1))
            if attempt < _MAX_RETRIES:
                logger.warning(
                    f"SMTP error sending to {to} (attempt {attempt}/{_MAX_RETRIES}): "
                    f"{exc} — retrying in {wait:.0f}s"
                )
                time.sleep(wait)
            else:
                logger.error(
                    f"Failed to send to {to} after {_MAX_RETRIES} attempts: {exc}"
                )

    return False, last_error


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — DELIVERY LOG
# ══════════════════════════════════════════════════════════════════════════════

class DeliveryRecord(NamedTuple):
    timestamp:    str
    email:        str
    region_plan:  str
    pdf_filename: str
    status:       str   # "sent" | "failed" | "skipped" | "dry_run"
    error:        str


def _init_log_writer(log_path: pathlib.Path):
    """Open the delivery log CSV and return (file_handle, csv.writer)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not log_path.exists()
    fh     = log_path.open("a", encoding="utf-8", newline="")
    writer = csv.writer(fh)
    if is_new:
        writer.writerow(DeliveryRecord._fields)
    return fh, writer


def _log_delivery(
    writer,
    *,
    email:        str,
    region_plan:  str,
    pdf_path:     pathlib.Path | None,
    status:       str,
    error:        str = "",
) -> None:
    writer.writerow(DeliveryRecord(
        timestamp    = datetime.now(timezone.utc).isoformat(),
        email        = email,
        region_plan  = region_plan,
        pdf_filename = pdf_path.name if pdf_path else "N/A",
        status       = status,
        error        = error,
    ))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — MAIN DELIVERY LOOP
# ══════════════════════════════════════════════════════════════════════════════

def deliver(
    csv_path:      pathlib.Path,
    *,
    report_month:  str | None = None,
    dry_run:       bool       = False,
    filter_region: str | None = None,
    send_delay_s:  float      = 1.0,
) -> None:
    """
    Main entry point for the delivery pipeline.

    1. Load subscribers from CSV
    2. Generate one PDF per unique region
    3. For each subscriber, build and send the personalised email
    4. Write a delivery log CSV to reports/
    """
    report_month = report_month or datetime.now().strftime("%B %Y")
    today_tag    = datetime.now().strftime("%Y-%m-%d")
    log_path     = REPORTS_DIR / f"delivery_log_{today_tag}.csv"

    # -- Load SMTP config early so config errors surface before generation ---
    smtp_config: SmtpConfig | None = None
    if not dry_run:
        try:
            smtp_config = _load_smtp_config()
        except ValueError as exc:
            logger.error(str(exc))
            sys.exit(1)

    # -- Load subscribers ---------------------------------------------------
    subscribers = load_subscribers(csv_path)
    if filter_region:
        subscribers = [s for s in subscribers
                       if s.region_plan.lower() == filter_region.lower()]
        logger.info(f"Filter applied: showing {len(subscribers)} subscriber(s) "
                    f"for region '{filter_region}'")

    if not subscribers:
        logger.warning("No subscribers to deliver to. Exiting.")
        return

    # -- Generate PDFs (one per region) ------------------------------------
    logger.info("-" * 60)
    logger.info("PHASE 1 — PDF Generation")
    logger.info("-" * 60)
    region_pdfs = generate_region_pdfs(
        subscribers,
        report_month,
        dry_run        = dry_run,
        filter_region  = filter_region,
    )

    # -- Delivery loop -------------------------------------------------------
    logger.info("-" * 60)
    logger.info("PHASE 2 — Email Delivery")
    logger.info("-" * 60)

    log_fh, log_writer = _init_log_writer(log_path)
    sent_count  = 0
    fail_count  = 0
    skip_count  = 0

    try:
        for idx, sub in enumerate(subscribers, start=1):
            cfg      = _region_cfg(sub.region_plan)
            pdf_path = region_pdfs.get(sub.region_plan)

            if pdf_path is None:
                logger.warning(
                    f"[{idx}/{len(subscribers)}] Skipping {sub.email} "
                    f"— no PDF for region '{sub.region_plan}'"
                )
                _log_delivery(
                    log_writer,
                    email=sub.email, region_plan=sub.region_plan,
                    pdf_path=None, status="skipped",
                    error="PDF generation failed for this region",
                )
                skip_count += 1
                continue

            logger.info(
                f"[{idx}/{len(subscribers)}] Sending to {sub.email} "
                f"— {cfg['label']} ({pdf_path.name})"
            )

            # In dry-run mode there is no real PDF on disk — skip building the
            # MIME message (which requires opening the file) and log directly.
            if dry_run:
                logger.info(f"[DRY-RUN] Would email '{sub.email}' with {pdf_path.name}")
                _log_delivery(
                    log_writer, email=sub.email, region_plan=sub.region_plan,
                    pdf_path=pdf_path, status="dry_run", error="",
                )
                sent_count += 1
                continue

            msg = _build_email(
                to_email     = sub.email,
                region       = cfg["label"],
                region_plan  = sub.region_plan,
                pdf_path     = pdf_path,
                from_addr    = smtp_config.from_addr,
                report_month = report_month,
            )

            try:
                success, error_msg = _send_one(msg, sub.email, smtp_config)
            except smtplib.SMTPAuthenticationError:
                # Auth failure is fatal — abort remaining sends
                logger.error(
                    "SMTP authentication failed — aborting delivery.\n"
                    "  Check SMTP_USER and SMTP_PASSWORD environment variables."
                )
                _log_delivery(
                    log_writer, email=sub.email, region_plan=sub.region_plan,
                    pdf_path=pdf_path, status="failed",
                    error="SMTP authentication error — delivery aborted",
                )
                fail_count += 1
                break

            _log_delivery(
                log_writer, email=sub.email, region_plan=sub.region_plan,
                pdf_path=pdf_path, status="sent" if success else "failed",
                error=error_msg,
            )

            if success:
                sent_count += 1
            else:
                fail_count += 1

            # Rate-limit between sends (avoid triggering spam filters)
            if idx < len(subscribers) and send_delay_s > 0 and not dry_run:
                time.sleep(send_delay_s)

    finally:
        log_fh.flush()
        log_fh.close()

    # -- Summary ---------------------------------------------------------------
    total = len(subscribers)
    logger.info("=" * 60)
    logger.info("  DELIVERY SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Total subscribers : {total}")
    logger.info(f"  Sent              : {sent_count}")
    logger.info(f"  Failed            : {fail_count}")
    logger.info(f"  Skipped           : {skip_count}")
    logger.info(f"  Log file          : {log_path}")
    logger.info("=" * 60)

    if fail_count:
        logger.warning(
            f"{fail_count} email(s) failed. "
            f"Check {log_path.name} for details."
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — CLI
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
        description="GameRadar AI — Automated Weekly Report Delivery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Environment variables (required unless --dry-run):
              SMTP_HOST       Mail server  (default: smtp.gmail.com)
              SMTP_PORT       Port         (default: 587)
              SMTP_USER       Sender login
              SMTP_PASSWORD   Sender password / app-password
              SMTP_FROM       Display name + address (default: SMTP_USER)
              SMTP_SSL        Set to 'true' for port-465 SSL mode

            Examples:
              python delivery.py --dry-run
              python delivery.py --region "Korea LCK" --month "April 2026"
              python delivery.py --csv custom_subscribers.csv --delay 2
        """),
    )

    parser.add_argument(
        "--csv", "-c",
        default=str(DEFAULT_CSV),
        help=f"Path to subscribers CSV (default: {DEFAULT_CSV.name})",
    )
    parser.add_argument(
        "--region", "-r",
        default=None,
        metavar="REGION",
        help="Deliver only to subscribers of this region (exact match, case-insensitive)",
    )
    parser.add_argument(
        "--month", "-m",
        default=None,
        help="Reporting period, e.g. 'April 2026' (default: current month)",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Delay in seconds between sends (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate subscribers and PDFs but do NOT send any emails",
    )

    args = parser.parse_args()

    deliver(
        csv_path      = pathlib.Path(args.csv),
        report_month  = args.month,
        dry_run       = args.dry_run,
        filter_region = args.region,
        send_delay_s  = args.delay,
    )
