"""
data_sync.py — GameRadar AI Data Sync
======================================
Downloads the latest /bronze JSON files from the GitHub repository via the
GitHub Contents API, deduplicates against existing records, normalises game
time units to minutes and date strings to ISO-8601, computes Activity_Level,
and writes master_rookie.json containing only players with Activity_Level > 70.

Usage
-----
    python data_sync.py
    python data_sync.py --repo marcelodanieldm/gameradar --branch main
    python data_sync.py --output master_rookie.json --threshold 70
    python data_sync.py --git-pull          # prefer git pull over API
    python data_sync.py --dry-run           # print stats without writing output
    python data_sync.py --token ghp_xxx     # GitHub PAT (avoids 60 req/h limit)
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests
from loguru import logger

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_REPO      = "marcelodanieldm/gameradar"
DEFAULT_BRANCH    = "main"
DEFAULT_OUTPUT    = pathlib.Path("master_rookie.json")
BRONZE_REMOTE_DIR = "bronze"
BRONZE_LOCAL_DIR  = pathlib.Path("bronze")

GITHUB_API_BASE   = "https://api.github.com"
GITHUB_RAW_BASE   = "https://raw.githubusercontent.com"

# DoD #1 — connectivity: any single JSON download must complete in < 5 s
DOWNLOAD_TIMEOUT_SEC = 5

# Activity_Level weights (no consistency_score available)
W_GAMES  = 0.60   # games_analyzed / 100  — main activity signal
W_WR     = 0.25   # win_rate / 100
W_KDA    = 0.15   # kda / 10.0

# Activity_Level weights (consistency_score available)
W_GAMES_C = 0.50
W_WR_C    = 0.20
W_KDA_C   = 0.10
W_CONS    = 0.20   # consistency_score / 100

# Date formats to try when parsing non-standard date strings
_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
]

# Field-name patterns that indicate a time value and its unit
_TIME_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"_seconds?$|^seconds?$", re.I), "seconds"),
    (re.compile(r"_secs?$|^secs?$",       re.I), "seconds"),
    (re.compile(r"_hours?$|^hours?$",      re.I), "hours"),
    (re.compile(r"_hrs?$|^hrs?$",          re.I), "hours"),
    (re.compile(r"_mins?$|^mins?$",        re.I), "minutes"),
    (re.compile(r"_minutes?$|^minutes?$",  re.I), "minutes"),
]

# Field-name patterns for date values
_DATE_FIELD_PATTERNS = re.compile(
    r"date|created_at|updated_at|timestamp|joined|registered|born", re.I
)


# ──────────────────────────────────────────────────────────────────────────────
# Logger setup
# ──────────────────────────────────────────────────────────────────────────────

def _configure_logger() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> │ "
            "<level>{level: <8}</level> │ "
            "<cyan>{function: <30}</cyan> │ "
            "{message}"
        ),
        colorize=True,
        level="DEBUG",
    )


# ──────────────────────────────────────────────────────────────────────────────
# GitHub API helpers
# ──────────────────────────────────────────────────────────────────────────────

def _api_headers(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_get(url: str, token: str | None, timeout: int = DOWNLOAD_TIMEOUT_SEC) -> Any:
    """GET from GitHub API with basic error handling and 5-second DoD timing."""
    t0   = time.perf_counter()
    resp = requests.get(url, headers=_api_headers(token), timeout=timeout)
    elapsed = time.perf_counter() - t0
    if elapsed > DOWNLOAD_TIMEOUT_SEC:
        logger.warning(
            f"DoD #1 BREACH: API call took {elapsed:.2f}s (limit {DOWNLOAD_TIMEOUT_SEC}s) — {url}"
        )
    else:
        logger.debug(f"  GET {elapsed:.2f}s ← {url}")
    if resp.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit exceeded (60 req/h unauthenticated). "
            "Pass --token <GITHUB_PAT> to raise it to 5000 req/h."
        )
    resp.raise_for_status()
    return resp.json()


def _list_bronze_sources(repo: str, branch: str, token: str | None) -> list[dict]:
    """Return list of subdirectory entries under /bronze."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{BRONZE_REMOTE_DIR}?ref={branch}"
    logger.debug(f"Listing bronze sources → {url}")
    entries = _api_get(url, token)
    dirs = [e for e in entries if e.get("type") == "dir"]
    logger.info(f"Found {len(dirs)} source(s) in remote /bronze: {[d['name'] for d in dirs]}")
    return dirs


def _list_source_files(source_entry: dict, repo: str, branch: str, token: str | None) -> list[dict]:
    """Return list of .json file entries inside a bronze source directory."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{source_entry['path']}?ref={branch}"
    entries = _api_get(url, token)
    return [e for e in entries if e.get("name", "").endswith(".json")]


def _download_file(file_entry: dict, token: str | None) -> list[dict]:
    """
    Download and decode a single bronze JSON file from the repository.
    Uses the raw download_url to avoid an extra API round-trip.
    Enforces the DoD #1 connectivity SLA: download must complete in < 5 s.
    """
    raw_url = file_entry.get("download_url") or file_entry.get("url")
    t0   = time.perf_counter()
    resp = requests.get(raw_url, headers=_api_headers(token), timeout=DOWNLOAD_TIMEOUT_SEC)
    elapsed = time.perf_counter() - t0
    if elapsed > DOWNLOAD_TIMEOUT_SEC:
        logger.warning(
            f"DoD #1 BREACH: download took {elapsed:.2f}s "
            f"(limit {DOWNLOAD_TIMEOUT_SEC}s) — {file_entry.get('name', raw_url)}"
        )
    else:
        logger.debug(
            f"  Downloaded {file_entry.get('name', '?')} in {elapsed:.2f}s ✓"
        )
    resp.raise_for_status()

    # The download_url returns raw bytes; the API url returns base64-encoded JSON
    if "download_url" in file_entry and file_entry["download_url"]:
        content = resp.text
    else:
        payload = resp.json()
        content = base64.b64decode(payload["content"]).decode("utf-8-sig")

    data = json.loads(content)
    return data if isinstance(data, list) else [data]


# ──────────────────────────────────────────────────────────────────────────────
# git pull fallback
# ──────────────────────────────────────────────────────────────────────────────

def _sync_via_git_pull() -> None:
    """Run `git pull origin main` to update the local working copy."""
    logger.info("Using git pull to sync /bronze …")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        capture_output=True,
        text=True,
        cwd=pathlib.Path(__file__).parent,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git pull failed:\n{result.stderr}")
    logger.success(f"git pull → {result.stdout.strip()}")


# ──────────────────────────────────────────────────────────────────────────────
# Local bronze loader (post git-pull path)
# ──────────────────────────────────────────────────────────────────────────────

def _load_local_bronze() -> dict[str, list[dict]]:
    """
    Read all *.json files under BRONZE_LOCAL_DIR.
    Returns {source_name: [record, …]}.
    """
    result: dict[str, list[dict]] = {}
    for source_dir in sorted(BRONZE_LOCAL_DIR.iterdir()):
        if not source_dir.is_dir():
            continue
        source = source_dir.name
        records: list[dict] = []
        for json_file in sorted(source_dir.glob("*.json")):
            try:
                raw = json.loads(json_file.read_text(encoding="utf-8-sig"))
                batch = raw if isinstance(raw, list) else [raw]
                records.extend(batch)
                logger.debug(f"  Loaded {len(batch):3d} record(s) from {json_file.name}")
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"  Skipping {json_file} — {exc}")
        if records:
            result[source] = records
            logger.info(f"  [{source}] {len(records)} record(s) from local disk")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation — Game times
# ──────────────────────────────────────────────────────────────────────────────

def _detect_time_unit(field_name: str) -> str | None:
    """
    Return 'seconds', 'minutes', or 'hours' based on the field name suffix.
    Returns None if the field doesn't look like a time field.
    """
    for pattern, unit in _TIME_PATTERNS:
        if pattern.search(field_name):
            return unit
    return None


def _hhmmss_to_minutes(value: str) -> float | None:
    """Parse 'HH:MM:SS' or 'MM:SS' string and return total minutes."""
    parts = value.strip().split(":")
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return round(h * 60 + m + s / 60, 4)
        if len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return round(m + s / 60, 4)
    except (ValueError, TypeError):
        pass
    return None


def _to_minutes(value: Any, unit: str) -> float | None:
    """Convert a numeric or HH:MM:SS time value to minutes."""
    # HH:MM:SS string
    if isinstance(value, str) and ":" in value:
        return _hhmmss_to_minutes(value)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if unit == "seconds":
        return round(numeric / 60, 4)
    if unit == "hours":
        return round(numeric * 60, 4)
    # already minutes
    return round(numeric, 4)


def normalize_game_times(record: dict) -> tuple[dict, int]:
    """
    Walk all nested numeric fields. Where a key matches a time pattern,
    convert the value to minutes and rename the key to end in '_minutes'.
    Returns (normalised_record, changes_made).
    """
    changes = 0

    def _walk(obj: Any) -> Any:
        nonlocal changes
        if isinstance(obj, dict):
            new_obj: dict = {}
            for k, v in obj.items():
                unit = _detect_time_unit(k)
                if unit is not None:
                    converted = _to_minutes(v, unit)
                    if converted is not None:
                        # Build new key ending in '_minutes'
                        new_key = re.sub(
                            r"_?(seconds?|secs?|hours?|hrs?|mins?|minutes?)$",
                            "_minutes",
                            k,
                            flags=re.I,
                        ).rstrip("_")
                        if new_key == k and unit == "minutes":
                            new_obj[k] = converted
                        else:
                            new_obj[new_key] = converted
                            if new_key != k or converted != v:
                                changes += 1
                            logger.debug(
                                f"    TIME  '{k}' ({unit}) = {v!r} → '{new_key}' = {converted} min"
                            )
                        continue
                new_obj[k] = _walk(v)
            return new_obj
        if isinstance(obj, list):
            return [_walk(i) for i in obj]
        return obj

    normalised = _walk(record)
    return normalised, changes


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation — Dates → ISO-8601
# ──────────────────────────────────────────────────────────────────────────────

def _parse_date(value: str) -> str | None:
    """
    Try to parse a date string with multiple formats.
    Returns ISO-8601 UTC string or None if unparseable.
    """
    value = value.strip()
    # Already ISO-8601 — validate and return
    if re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?Z?)?$", value):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass

    # Try epoch timestamp
    if re.match(r"^\d{10,13}$", value):
        ts = int(value) / (1000 if len(value) == 13 else 1)
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Try known formats
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return None


def normalize_dates(record: dict) -> tuple[dict, int]:
    """
    Walk all string fields whose key matches a date-like pattern.
    Convert values to ISO-8601 UTC.
    Returns (normalised_record, changes_made).
    """
    changes = 0

    def _walk(obj: Any) -> Any:
        nonlocal changes
        if isinstance(obj, dict):
            return {
                k: _process_field(k, v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_walk(i) for i in obj]
        return obj

    def _process_field(key: str, value: Any) -> Any:
        nonlocal changes
        if isinstance(value, str) and _DATE_FIELD_PATTERNS.search(key):
            iso = _parse_date(value)
            if iso and iso != value:
                changes += 1
                logger.debug(f"    DATE  '{key}': '{value}' → '{iso}'")
                return iso
        if isinstance(value, (dict, list)):
            return _walk(value)
        return value

    normalised = _walk(record)
    return normalised, changes


# ──────────────────────────────────────────────────────────────────────────────
# Activity Level computation
# ──────────────────────────────────────────────────────────────────────────────

def compute_activity_level(record: dict) -> float:
    """
    Compute Activity_Level ∈ [0, 100] from a bronze record's stats.

    Weights (when consistency_score unavailable):
      60 % games_analyzed (/ 100)
      25 % win_rate       (/ 100)
      15 % kda            (/ 10)

    Weights (when consistency_score available):
      50 % games_analyzed
      20 % win_rate
      10 % kda
      20 % consistency_score (/ 100)
    """
    stats = record.get("stats", {})
    if not isinstance(stats, dict):
        return 0.0

    games  = float(stats.get("games_analyzed", 0) or 0)
    wr     = float(stats.get("win_rate",       0) or 0)
    kda    = float(stats.get("kda",            0) or 0)
    cons   = stats.get("consistency_score")

    g_norm = min(1.0, games / 100.0)
    w_norm = min(1.0, wr    / 100.0)
    k_norm = min(1.0, kda   / 10.0)

    if cons is not None:
        c_norm = min(1.0, float(cons) / 100.0)
        level  = (g_norm * W_GAMES_C + w_norm * W_WR_C + k_norm * W_KDA_C + c_norm * W_CONS) * 100
    else:
        level  = (g_norm * W_GAMES + w_norm * W_WR + k_norm * W_KDA) * 100

    return round(min(100.0, level), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────────────────────────────────────

def _dedup_key(record: dict, source: str) -> str:
    """Composite dedup key: lowercased nickname + source."""
    nickname = str(record.get("nickname") or record.get("name") or "unknown").lower().strip()
    return f"{nickname}::{source}"


def deduplicate(
    new_records: dict[str, list[dict]],
    existing_records: list[dict],
) -> tuple[list[dict], int, int]:
    """
    Merge new_records (by source) with existing_records (already-synced list).
    Players already present in existing are skipped.

    Returns (merged_list, new_count, duplicate_count).
    """
    seen: set[str] = set()
    merged: list[dict] = []

    # Seed seen keys from existing master
    for rec in existing_records:
        key = _dedup_key(rec, rec.get("_source", ""))
        seen.add(key)
        merged.append(rec)

    new_count = dup_count = 0

    for source, records in new_records.items():
        for rec in records:
            key = _dedup_key(rec, source)
            if key in seen:
                logger.debug(f"  DUP   [{source}] {rec.get('nickname')!r} — already in master")
                dup_count += 1
                continue
            seen.add(key)
            rec["_source"] = source
            merged.append(rec)
            new_count += 1

    return merged, new_count, dup_count


# ──────────────────────────────────────────────────────────────────────────────
# Full pipeline per record: normalise + enrich
# ──────────────────────────────────────────────────────────────────────────────

def process_record(record: dict) -> dict:
    """Apply all normalisation steps and inject computed fields."""
    record, time_changes  = normalize_game_times(record)
    record, date_changes  = normalize_dates(record)
    activity              = compute_activity_level(record)
    record["activity_level"] = activity

    if time_changes or date_changes:
        logger.debug(
            f"  NORM  {record.get('nickname')!r} — "
            f"{time_changes} time, {date_changes} date field(s) normalised"
        )
    return record


# ──────────────────────────────────────────────────────────────────────────────
# Output writer
# ──────────────────────────────────────────────────────────────────────────────

def write_master_rookie(players: list[dict], output: pathlib.Path) -> None:
    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "_meta": {
            "run_ts":         run_ts,
            "total_players":  len(players),
            "filter":         "activity_level > 70",
            "activity_formula": (
                "60%×(games_analyzed/100) + 25%×(win_rate/100) + 15%×(kda/10)  "
                "[+20%×(consistency_score/100) when available]"
            ),
        },
        "players": players,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.success(f"Written → {output}  ({len(players)} players)")


# ──────────────────────────────────────────────────────────────────────────────
# GitHub API download orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def download_via_api(
    repo: str,
    branch: str,
    token: str | None,
) -> dict[str, list[dict]]:
    """
    Download all .json files from /bronze/<source>/ via the GitHub Contents API.
    Returns {source_name: [record, …]}.
    """
    logger.info(f"Connecting to GitHub API → {repo} (branch: {branch})")
    sources = _list_bronze_sources(repo, branch, token)

    result: dict[str, list[dict]] = {}
    total_files = total_records = 0

    for src_entry in sources:
        source = src_entry["name"]
        logger.info(f"  ↓  Fetching source: {source}")

        files = _list_source_files(src_entry, repo, branch, token)
        if not files:
            logger.warning(f"    No JSON files found in /bronze/{source} — skipping")
            continue

        # Only download the most-recent file (lexicographically last by filename = latest date)
        latest = sorted(files, key=lambda f: f["name"])[-1]
        logger.debug(f"    Latest file: {latest['name']} ({latest.get('size', '?')} bytes)")

        try:
            records = _download_file(latest, token)
            logger.info(f"    ✓  {len(records):3d} record(s) from {latest['name']}")
            result[source] = records
            total_files   += 1
            total_records += len(records)
            # Be a good citizen: small delay between requests
            time.sleep(0.3)
        except Exception as exc:
            logger.error(f"    ✗  Failed to download {latest['name']}: {exc}")

    logger.success(
        f"GitHub API download complete — "
        f"{total_files} file(s), {total_records} record(s) across {len(result)} source(s)"
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sync /bronze from GitHub → deduplicate → normalise → master_rookie.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--repo",      default=DEFAULT_REPO,   help="GitHub repo (owner/name)")
    p.add_argument("--branch",    default=DEFAULT_BRANCH, help="Branch to sync from")
    p.add_argument("--token",     default=None,           help="GitHub PAT (raises rate limit to 5000/h)")
    p.add_argument("--output",    default=str(DEFAULT_OUTPUT), help="Output file path")
    p.add_argument("--threshold", type=float, default=70.0,    help="Minimum Activity_Level (default: 70)")
    p.add_argument("--git-pull",  action="store_true",    help="Use git pull instead of GitHub API")
    p.add_argument("--dry-run",   action="store_true",    help="Print stats without writing output")
    return p


def main() -> int:
    _configure_logger()
    args = build_parser().parse_args()
    output = pathlib.Path(args.output)

    # ── STEP 1: Download bronze data ─────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 1 — Download bronze data from GitHub")
    logger.info("=" * 60)

    raw_by_source: dict[str, list[dict]] = {}

    if args.git_pull:
        try:
            _sync_via_git_pull()
            raw_by_source = _load_local_bronze()
        except Exception as exc:
            logger.error(f"git pull failed: {exc}. Falling back to GitHub API …")
            raw_by_source = download_via_api(args.repo, args.branch, args.token)
    else:
        try:
            raw_by_source = download_via_api(args.repo, args.branch, args.token)
        except Exception as exc:
            logger.warning(f"GitHub API error: {exc}. Falling back to git pull …")
            try:
                _sync_via_git_pull()
                raw_by_source = _load_local_bronze()
            except Exception as pull_exc:
                logger.critical(f"Both sync methods failed: {pull_exc}")
                return 1

    total_raw = sum(len(v) for v in raw_by_source.values())
    logger.info(
        f"Downloaded {total_raw} raw record(s) from "
        f"{len(raw_by_source)} source(s): {sorted(raw_by_source)}"
    )

    # ── STEP 2: Load existing master (for dedup) ─────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 2 — Load existing master_rookie.json for deduplication")
    logger.info("=" * 60)

    existing: list[dict] = []
    if output.exists():
        try:
            existing_payload = json.loads(output.read_text(encoding="utf-8"))
            existing = existing_payload.get("players", [])
            logger.info(f"Found existing master with {len(existing)} player(s)")
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(f"Could not read existing master ({exc}) — starting fresh")
    else:
        logger.info("No existing master found — starting fresh")

    # ── STEP 3: Deduplicate ───────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 3 — Deduplicate")
    logger.info("=" * 60)

    merged, new_count, dup_count = deduplicate(raw_by_source, existing)
    logger.info(f"Dedup result: {new_count} new, {dup_count} duplicate(s), {len(merged)} total")

    # ── STEP 4: Normalise units ───────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 4 — Normalise game times & dates")
    logger.info("=" * 60)

    processed: list[dict] = []
    time_changes_total = date_changes_total = 0

    for rec in merged:
        rec, tc = normalize_game_times(rec)
        rec, dc = normalize_dates(rec)
        time_changes_total += tc
        date_changes_total += dc
        processed.append(rec)

    logger.info(
        f"Normalisation complete — "
        f"{time_changes_total} time field(s), {date_changes_total} date field(s) converted"
    )

    # ── STEP 5: Compute Activity_Level ───────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 5 — Compute Activity_Level for each player")
    logger.info("=" * 60)

    for rec in processed:
        rec["activity_level"] = compute_activity_level(rec)

    by_level = sorted(processed, key=lambda r: r["activity_level"], reverse=True)
    for rec in by_level:
        marker = "✓" if rec["activity_level"] > args.threshold else "✗"
        logger.info(
            f"  {marker}  {rec.get('nickname', '?'):20s} "
            f"[{rec.get('_source', '?'):12s}] "
            f"activity={rec['activity_level']:5.1f}%  "
            f"games={rec.get('stats', {}).get('games_analyzed', '?'):>4}  "
            f"wr={rec.get('stats', {}).get('win_rate', '?'):>5}%  "
            f"kda={rec.get('stats', {}).get('kda', '?')}"
        )

    # ── STEP 6: Filter rookies ────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"STEP 6 — Filter: activity_level > {args.threshold}%")
    logger.info("=" * 60)

    rookies = [r for r in by_level if r["activity_level"] > args.threshold]
    excluded = len(by_level) - len(rookies)

    logger.info(f"Kept: {len(rookies)} player(s)  |  Excluded: {excluded} player(s)")

    if not rookies:
        logger.warning(
            f"No players passed the {args.threshold}% threshold. "
            "Lower --threshold or ingest more data."
        )

    # ── STEP 7: Write output ──────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"STEP 7 — Write {output}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info(f"[DRY RUN] Would write {len(rookies)} player(s) to {output} — skipping")
    else:
        write_master_rookie(rookies, output)

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("━" * 60)
    logger.info("SYNC COMPLETE")
    logger.info(f"  Raw downloaded   : {total_raw}")
    logger.info(f"  New (not in master): {new_count}")
    logger.info(f"  Duplicates skipped : {dup_count}")
    logger.info(f"  Time fields fixed  : {time_changes_total}")
    logger.info(f"  Date fields fixed  : {date_changes_total}")
    logger.info(f"  Passed threshold   : {len(rookies)} / {len(processed)}")
    logger.info(f"  Output             : {output.resolve()}")
    logger.info("━" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
