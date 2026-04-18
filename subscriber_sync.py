"""
subscriber_sync.py — GameRadar AI · Stripe → subscribers.csv Sync
==================================================================

Pulls all completed Rookie Plan checkouts from Stripe and appends any new
subscribers to the local subscribers.csv file — ready for delivery.py to
consume immediately after.

RUN ORDER (every Monday before delivery.py):
    1.  python subscriber_sync.py      ← YOU ARE HERE
    2.  python delivery.py

Usage
-----
    python subscriber_sync.py                    # sync from Stripe, update CSV
    python subscriber_sync.py --dry-run          # show what would change, no write
    python subscriber_sync.py --since 2026-01-01 # only look at events after a date
    python subscriber_sync.py --limit 100        # cap API pages (100 events each)

Environment variables (required)
---------------------------------
    STRIPE_SECRET_KEY   Your Stripe secret key (sk_live_… or sk_test_…)

    Set in .env or export before running:
        $env:STRIPE_SECRET_KEY = "sk_test_..."

Region detection order
-----------------------
    1. Stripe Payment Link custom field  (field label: "region")
    2. Stripe checkout session metadata  (key: "region")
    3. Customer metadata                 (key: "region")
    → Falls back to "Global" if none found

Custom field setup in Stripe Dashboard
----------------------------------------
    Payment Link → Edit → Add custom field
        Label:  region
        Type:   Dropdown
        Options: india | korea | vietnam | thailand | china | sea | japan
    The raw option VALUE (not label) is stored in custom_fields[].dropdown.value
"""

from __future__ import annotations

import argparse
import csv
import os
import pathlib
import re
import sys
import threading
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env support is optional

try:
    import stripe as _stripe
    _stripe.api_version = "2024-04-10"
except ImportError:
    logger.error(
        "stripe package is not installed.\n"
        "  Run:  pip install stripe==8.2.0\n"
        "  Or:   pip install -r requirements.txt"
    )
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR         = pathlib.Path(__file__).parent
SUBSCRIBERS_PATH = BASE_DIR / "subscribers.csv"
SYNC_LOG_PATH    = BASE_DIR / "reports" / "subscriber_sync_log.csv"

_CSV_FIELDNAMES = ["email", "region_plan", "messenger", "plan", "source", "subscribed_at"]

# ──────────────────────────────────────────────────────────────────────────────
# Region mapping — must stay consistent with delivery.py REGION_CONFIG
# ──────────────────────────────────────────────────────────────────────────────

# Stripe stores the raw dropdown option value (lowercase slug).
# This maps it to the canonical region_plan label that delivery.py expects.
_REGION_MAP: dict[str, str] = {
    "india":    "India",
    "korea":    "Korea LCK",
    "vietnam":  "Vietnam VCS",
    "thailand": "Thailand",
    "china":    "China LPL",
    "sea":      "Asia Pacific",
    "japan":    "Japan LJL",
    "global":   "Global",
    # Accept some natural-language variants too (in case of Stripe metadata typos)
    "india tec":          "India",
    "korea lck":          "Korea LCK",
    "vietnam vcs":        "Vietnam VCS",
    "southeast asia":     "Asia Pacific",
    "asia pacific":       "Asia Pacific",
    "china lpl":          "China LPL",
    "japan ljl":          "Japan LJL",
}

_FALLBACK_REGION = "Global"


def _canonical_region(raw: str) -> str:
    """Normalise a free-form region string to a canonical region_plan label."""
    key = raw.strip().lower()
    return _REGION_MAP.get(key, _FALLBACK_REGION)


# ──────────────────────────────────────────────────────────────────────────────
# Input validation & sanitisation (OWASP A03 — injection)
# ──────────────────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,}$"
)


def _valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def _csv_safe(value: str) -> str:
    """Prevent CSV formula-injection (OWASP A03:2021 — CWE-1236)."""
    value = value.strip()
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r", "|"):
        value = "'" + value
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Stripe helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise SystemExit(
            "STRIPE_SECRET_KEY environment variable is not set.\n"
            "  Export it or add it to your .env file:\n"
            "    STRIPE_SECRET_KEY=sk_live_..."
        )
    if not key.startswith(("sk_live_", "sk_test_")):
        raise SystemExit(
            f"STRIPE_SECRET_KEY looks invalid: {key[:12]}…\n"
            "  It must start with 'sk_live_' or 'sk_test_'"
        )
    return key


def _extract_region_from_session(session: object) -> str:
    """
    Try to extract the region value from a checkout session in this order:
      1. custom_fields[].dropdown.value  (Payment Link custom field)
      2. session.metadata['region']
      3. customer.metadata['region']  (if session has customer_details)
    Returns canonical region_plan string.
    """
    # 1. Payment Link custom field (dropdown)
    try:
        for field in (session.custom_fields or []):
            label_key = (field.key or "").lower()
            if label_key == "region" and field.type == "dropdown":
                raw = (field.dropdown.value or "").strip()
                if raw:
                    return _canonical_region(raw)
    except AttributeError:
        pass

    # 2. Session metadata
    try:
        meta_region = (session.metadata or {}).get("region", "")
        if meta_region:
            return _canonical_region(meta_region)
    except AttributeError:
        pass

    # 3. Customer-level metadata
    try:
        cust_region = (session.customer_details or {}).get("region", "")
        if cust_region:
            return _canonical_region(cust_region)
    except (AttributeError, TypeError):
        pass

    return _FALLBACK_REGION


def _extract_messenger_from_session(session: object) -> str:
    """Pull Discord/Telegram username from custom_fields or metadata."""
    try:
        for field in (session.custom_fields or []):
            label_key = (field.key or "").lower()
            if label_key in ("messenger", "discord", "telegram") and field.type == "text":
                return _csv_safe((field.text.value or "").strip()[:64])
    except AttributeError:
        pass
    try:
        return _csv_safe(
            (session.metadata or {}).get("messenger", "")[:64]
        )
    except AttributeError:
        return ""


def fetch_paid_subscribers(
    since_ts: Optional[int] = None,
    max_pages: int = 50,
) -> list[dict]:
    """
    List checkout sessions with payment_status=paid from Stripe.
    Returns a list of normalised subscriber dicts ready for CSV insertion.

    Parameters
    ----------
    since_ts    Unix timestamp.  Only sessions created ≥ this time are returned.
    max_pages   Safety cap on Stripe API pagination (100 results per page).
    """
    params: dict = {
        "payment_status": "paid",
        "limit":          100,
        "expand":         ["data.customer", "data.custom_fields"],
    }
    if since_ts:
        params["created"] = {"gte": since_ts}

    subscribers: list[dict] = []
    pages_fetched = 0
    seen_emails: set[str] = set()

    logger.info("Fetching paid checkout sessions from Stripe…")

    try:
        sessions = _stripe.checkout.Session.list(**params)
        while sessions and pages_fetched < max_pages:
            pages_fetched += 1
            for session in sessions.auto_paging_iter():
                email = (
                    getattr(session, "customer_email", None)
                    or (getattr(session, "customer_details", None) or {}).get("email", "")
                    or ""
                ).strip().lower()

                if not email:
                    logger.debug(f"  ⚠  Session {session.id} has no email — skipping")
                    continue
                if not _valid_email(email):
                    logger.warning(f"  ⚠  Invalid email in session {session.id}: {email!r}")
                    continue
                if email in seen_emails:
                    continue  # duplicate within this API batch
                seen_emails.add(email)

                region_plan = _extract_region_from_session(session)
                messenger   = _extract_messenger_from_session(session)
                created_ts  = getattr(session, "created", None)
                subscribed_at = (
                    datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    if created_ts else
                    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                )

                subscribers.append({
                    "email":          _csv_safe(email),
                    "region_plan":    _csv_safe(region_plan),
                    "messenger":      messenger,
                    "plan":           "rookie",
                    "source":         "stripe_checkout",
                    "subscribed_at":  subscribed_at,
                    "_session_id":    session.id,  # internal — not written to CSV
                })

    except _stripe.error.AuthenticationError:
        logger.error("Stripe authentication failed — check STRIPE_SECRET_KEY")
        sys.exit(1)
    except _stripe.error.StripeError as exc:
        logger.error(f"Stripe API error: {exc}")
        sys.exit(1)

    logger.info(f"  Stripe returned {len(subscribers)} unique paid subscriber(s)")
    return subscribers


# ──────────────────────────────────────────────────────────────────────────────
# CSV helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_existing_emails(csv_path: pathlib.Path) -> set[str]:
    """Return the set of emails already in subscribers.csv (lowercase)."""
    if not csv_path.exists():
        return set()
    emails: set[str] = set()
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                email = row.get("email", "").strip().lower()
                if email:
                    emails.add(email)
    except Exception as exc:
        logger.warning(f"Could not read {csv_path}: {exc}")
    return emails


_csv_write_lock = threading.Lock()


def append_subscribers(
    new_subs: list[dict],
    csv_path: pathlib.Path,
    dry_run: bool = False,
) -> int:
    """
    Append new_subs to csv_path.  Creates the file with a header if absent.
    Returns the number of rows actually written.
    Thread-safe via _csv_write_lock.
    """
    if not new_subs:
        return 0

    if dry_run:
        for sub in new_subs:
            logger.info(
                f"  [DRY-RUN] Would add: {sub['email']} → {sub['region_plan']}"
            )
        return len(new_subs)

    with _csv_write_lock:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = csv_path.exists()

        with csv_path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=_CSV_FIELDNAMES,
                extrasaction="ignore",  # drop _session_id etc.
            )
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_subs)

    return len(new_subs)


def write_sync_log(
    added: list[dict],
    skipped: int,
    dry_run: bool,
    log_path: pathlib.Path,
) -> None:
    """Append a summary row to the sync log CSV."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_path.exists()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with log_path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not file_exists:
            writer.writerow(
                ["sync_ts", "new_subscribers", "duplicates_skipped", "dry_run", "emails_added"]
            )
        emails_preview = "|".join(s["email"] for s in added[:10])
        if len(added) > 10:
            emails_preview += f"|…+{len(added) - 10} more"
        writer.writerow([ts, len(added), skipped, dry_run, emails_preview])


# ──────────────────────────────────────────────────────────────────────────────
# Region assignment validation
# ──────────────────────────────────────────────────────────────────────────────

# Full mapping from region_plan → report slug (mirrors delivery.py REGION_CONFIG)
_REPORT_SLUG: dict[str, str] = {
    "india":          "india",
    "korea lck":      "korea_lck",
    "vietnam vcs":    "vietnam_vcs",
    "thailand":       "thailand",
    "china lpl":      "china_lpl",
    "asia pacific":   "asia_pacific",
    "japan ljl":      "japan_ljl",
    "global":         "global",
}


def _report_slug(region_plan: str) -> str:
    return _REPORT_SLUG.get(region_plan.lower(), "global")


def validate_assignments(subs: list[dict]) -> None:
    """
    Log a per-region summary and confirm each subscriber will receive
    the correct report PDF.  Mirrors the logic in delivery.py so the
    operator can verify before running the delivery.
    """
    from collections import Counter
    counts: Counter = Counter(s["region_plan"] for s in subs)
    logger.info("─" * 55)
    logger.info("  Region assignment validation:")
    for region, n in sorted(counts.items()):
        slug = _report_slug(region)
        logger.info(f"    {region:<20} → {slug}_report.pdf  ({n} subscriber{'s' if n > 1 else ''})")
    logger.info("─" * 55)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync Stripe paid subscribers → subscribers.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
  # Normal weekly sync (before delivery.py)
  python subscriber_sync.py

  # Preview only — no CSV changes
  python subscriber_sync.py --dry-run

  # Only look at payments since a specific date
  python subscriber_sync.py --since 2026-04-01

  # Limit API pagination
  python subscriber_sync.py --limit 5

Run order (every Monday):
  1. python subscriber_sync.py
  2. python delivery.py
""",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without modifying subscribers.csv",
    )
    p.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Only sync Stripe sessions created on or after this date (UTC)",
        default=None,
    )
    p.add_argument(
        "--limit",
        metavar="N",
        type=int,
        default=50,
        help="Max API pages to fetch (100 sessions per page, default: 50)",
    )
    p.add_argument(
        "--csv",
        metavar="PATH",
        help=f"Path to subscribers CSV (default: {SUBSCRIBERS_PATH})",
        default=str(SUBSCRIBERS_PATH),
    )
    return p.parse_args()


def main() -> int:
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{function}</cyan> | {message}",
        colorize=True,
    )

    args = _parse_args()
    csv_path = pathlib.Path(args.csv)

    # ── Load Stripe key ────────────────────────────────────────────────────────
    _stripe.api_key = _load_stripe_key()
    key_preview = _stripe.api_key[:12] + "…"
    mode = "TEST" if _stripe.api_key.startswith("sk_test_") else "LIVE"
    logger.info(f"Stripe key loaded  ({mode} mode) — {key_preview}")

    if mode == "LIVE":
        logger.warning(
            "⚠  LIVE mode — real customer data will be read.  "
            "Use sk_test_ during development."
        )

    # ── Resolve --since to a Unix timestamp ───────────────────────────────────
    since_ts: Optional[int] = None
    if args.since:
        try:
            since_dt  = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            since_ts  = int(since_dt.timestamp())
            logger.info(f"Filtering sessions created ≥ {args.since} (ts={since_ts})")
        except ValueError:
            logger.error(f"Invalid --since date: {args.since!r}  (expected YYYY-MM-DD)")
            return 1

    # ── Fetch from Stripe ──────────────────────────────────────────────────────
    all_from_stripe = fetch_paid_subscribers(since_ts=since_ts, max_pages=args.limit)

    if not all_from_stripe:
        logger.info("No paid sessions found for the given criteria.")
        return 0

    # ── Deduplicate against existing CSV ──────────────────────────────────────
    existing_emails = _load_existing_emails(csv_path)
    logger.info(f"Existing subscribers in CSV: {len(existing_emails)}")

    new_subs = [
        s for s in all_from_stripe
        if s["email"] not in existing_emails
    ]
    duplicates = len(all_from_stripe) - len(new_subs)

    logger.info(
        f"New subscribers to add:    {len(new_subs)}"
        + (f"  ({duplicates} already present — skipped)" if duplicates else "")
    )

    if not new_subs:
        logger.success("subscribers.csv is already up-to-date.  Nothing to write.")
        write_sync_log([], duplicates, args.dry_run, SYNC_LOG_PATH)
        return 0

    # ── Validate region assignments ────────────────────────────────────────────
    validate_assignments(new_subs)

    # ── Write to CSV ───────────────────────────────────────────────────────────
    written = append_subscribers(new_subs, csv_path, dry_run=args.dry_run)

    if args.dry_run:
        logger.success(f"[DRY-RUN] Would have added {written} new subscriber(s).  CSV unchanged.")
    else:
        logger.success(
            f"✓ {written} new subscriber(s) added to {csv_path.name}"
        )
        # Per-subscriber confirmation
        for sub in new_subs:
            slug = _report_slug(sub["region_plan"])
            logger.info(
                f"  ✓ {sub['email']:<40}  {sub['region_plan']:<18}  "
                f"→ {slug}_report.pdf"
            )

    # ── Sync log ───────────────────────────────────────────────────────────────
    write_sync_log(new_subs, duplicates, args.dry_run, SYNC_LOG_PATH)

    if not args.dry_run:
        logger.info("")
        logger.info("Next step: run delivery.py to send this week's reports")
        logger.info("  python delivery.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
