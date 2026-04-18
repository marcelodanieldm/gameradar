"""
generate_rookie_report.py — GameRadar AI · Rookie Plan PDF Generator
=====================================================================

Loads player data from master_rookie.json (or silver_data.json as fallback),
scores and ranks via intelligence.py, builds the Jinja2 context with a fully
pre-computed SVG radar chart, then renders the report to PDF with WeasyPrint.

Usage
-----
    python generate_rookie_report.py
    python generate_rookie_report.py --output reports/rookie_april_2026.pdf
    python generate_rookie_report.py --region "Korea LCK" --month "April 2026"
    python generate_rookie_report.py --source silver   # use silver_data.json
    python generate_rookie_report.py --html-only       # skip WeasyPrint

Requirements
------------
    pip install weasyprint==62.3 jinja2==3.1.4
    (WeasyPrint on Windows also needs GTK — see https://doc.courtbouillon.org/weasyprint)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from loguru import logger

# ── Optional: intelligence.py (scoring + translation) ─────────────────────────
try:
    import intelligence as intel
    INTEL_OK = True
except ImportError:
    INTEL_OK = False
    logger.warning("intelligence.py not found — using simple fallback scoring")

# ── Optional: Jinja2 ──────────────────────────────────────────────────────────
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_OK = True
except ImportError:
    JINJA2_OK = False
    logger.error("Jinja2 not installed.  Run: pip install jinja2==3.1.4")

# ── Optional: WeasyPrint ──────────────────────────────────────────────────────
try:
    from weasyprint import HTML as WeasyHTML
    WEASY_OK = True
except ImportError:
    WEASY_OK = False
    logger.warning(
        "WeasyPrint not installed — HTML-only mode active.\n"
        "  pip install weasyprint==62.3  (GTK required on Windows)"
    )

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR       = pathlib.Path(__file__).parent
TEMPLATE_DIR   = BASE_DIR / "templates"
TEMPLATE_FILE  = "rookie_report.html"
MASTER_JSON    = BASE_DIR / "master_rookie.json"
SILVER_JSON    = BASE_DIR / "silver" / "silver_data.json"
REPORTS_DIR    = BASE_DIR / "reports"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DATA LOADING & NORMALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _load_players(source: str) -> list[dict]:
    """
    Load raw player records from the preferred source.

    source='master'  → master_rookie.json  (output of data_sync.py)
    source='silver'  → silver/silver_data.json  (output of bronze_to_silver.py)
    """
    if source == "silver":
        path = SILVER_JSON
    else:
        path = MASTER_JSON if MASTER_JSON.exists() else SILVER_JSON

    if not path.exists():
        logger.error(f"Data file not found: {path}")
        logger.error("Run data_sync.py (or bronze_to_silver.py) first.")
        sys.exit(1)

    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("players", payload) if isinstance(payload, dict) else payload

    if not isinstance(records, list) or not records:
        logger.error(f"No player records found in {path}")
        sys.exit(1)

    logger.info(f"Loaded {len(records)} raw records from {path.name}")
    return records


def _normalise_player(raw: dict) -> dict:
    """
    Flatten a player record from either master_rookie or silver_data format
    into a single canonical dict suitable for the template.

    master_rookie: nested 'stats' sub-dict, lowercase keys
    silver_data:   flat CamelCase keys (KDA, Win_Rate_Pct, etc.)
    """
    stats = raw.get("stats", {}) if isinstance(raw.get("stats"), dict) else {}

    def _f(key_snake: str, key_camel: str, default: float = 0.0) -> float:
        return float(stats.get(key_snake, raw.get(key_camel, default)))

    def _s(key_snake: str, key_camel: str, default: str = "") -> str:
        return str(raw.get(key_snake, raw.get(key_camel, default))).strip()

    kda   = _f("kda",           "KDA")
    wr    = _f("win_rate",      "Win_Rate_Pct")
    games = int(_f("games_analyzed", "Games_Analyzed"))
    consistency = _f("consistency_score", "Consistency_Index")

    return {
        "nickname":          _s("nickname",    "Nickname",   "Unknown"),
        "real_name":         _s("real_name",   "Real_Name"),
        "team":              _s("team",        "Team"),
        "role":              _s("role",        "Translated_Role", "Unknown"),
        "country":           _s("country",     "Region", "XX"),
        "server":            _s("server",      "Server"),
        "kda":               round(kda, 2),
        "win_rate":          round(wr, 1),
        "games_analyzed":    games,
        "consistency_index": round(consistency, 1),
        # gameradar_score will be filled after scoring
        "gameradar_score":   round(float(raw.get("final_score", raw.get("Calculated_Score", 0.0))), 4),
        "source":            _s("_source",     "Data_Source"),
        "photo_url":         _s("photo_url",   "Photo_URL"),
        "trend":             _s("trend",       "Trend"),
        "activity_level":    round(float(raw.get("activity_level", 0.0)), 1),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — SCORING
# ══════════════════════════════════════════════════════════════════════════════

_KDA_CAP    = 15.0
_GAMES_CAP  = 150.0
_W_KDA      = 0.35
_W_WR       = 0.45
_W_MF       = 0.20
_MULT       = {"KR": 1.20, "IN": 0.90}


def _fallback_score(p: dict) -> float:
    """Simple Rookie Plan scorer used when intelligence.py is unavailable."""
    kda_n  = min(p["kda"],            _KDA_CAP)   / _KDA_CAP   * 10.0
    wr_n   = min(p["win_rate"],       100.0)       / 100.0      * 10.0
    mf_n   = min(p["games_analyzed"], _GAMES_CAP)  / _GAMES_CAP * 10.0
    raw    = kda_n * _W_KDA + wr_n * _W_WR + mf_n * _W_MF
    mult   = _MULT.get(p["country"].upper(), 1.0)
    return min(round(raw * mult, 4), 10.0)


def _score_and_rank(players: list[dict]) -> list[dict]:
    """
    Score every player and return list sorted by final_score descending.
    Uses intelligence.rank_players() when available; falls back to
    _fallback_score() otherwise.
    """
    if INTEL_OK:
        import pandas as pd
        ranked_df = intel.rank_players(players)
        # Merge scored columns back onto normalised records
        scored_map: dict[str, float] = {}
        for _, row in ranked_df.iterrows():
            scored_map[str(row["nickname"])] = float(row.get("final_score", 0))
        for p in players:
            p["gameradar_score"] = scored_map.get(p["nickname"], p["gameradar_score"])
    else:
        for p in players:
            p["gameradar_score"] = _fallback_score(p)

    players.sort(key=lambda x: x["gameradar_score"], reverse=True)

    # score_pct drives the CSS progress bar (0–100)
    for p in players:
        p["score_pct"] = min(100, round(p["gameradar_score"] * 10))

    return players


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SVG RADAR CHART COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

_RADAR_CX       = 150.0     # SVG centre x
_RADAR_CY       = 150.0     # SVG centre y
_RADAR_MAX_R    = 95.0      # max radius (100% ring)
_RADAR_LABEL_R  = 114.0     # label placement radius
_RADAR_N_AXES   = 5
_RADAR_LABELS   = ["KDA", "Win Rate", "Consistency", "Match Freq", "Score"]


def _axis_angle(i: int) -> float:
    """Angle in radians for axis i (starting from top, clockwise)."""
    return math.radians(-90.0 + i * (360.0 / _RADAR_N_AXES))


def _polar_to_cartesian(r: float, angle: float) -> tuple[float, float]:
    return (
        round(_RADAR_CX + r * math.cos(angle), 2),
        round(_RADAR_CY + r * math.sin(angle), 2),
    )


def _polygon_points(normalised_values: list[float]) -> str:
    """
    Build SVG polygon points string from 5 normalised [0,1] values.
    Each value maps to a radial distance on its corresponding axis.
    """
    pts = []
    for i, v in enumerate(normalised_values):
        x, y = _polar_to_cartesian(_RADAR_MAX_R * max(0.0, min(1.0, v)), _axis_angle(i))
        pts.append(f"{x},{y}")
    return " ".join(pts)


def _grid_polygon(pct: float) -> str:
    """Regular pentagon at pct × max radius (for background grid)."""
    pts = []
    for i in range(_RADAR_N_AXES):
        x, y = _polar_to_cartesian(_RADAR_MAX_R * pct, _axis_angle(i))
        pts.append(f"{x},{y}")
    return " ".join(pts)


def _build_axes() -> list[dict]:
    """Pre-compute axis line endpoints and label positions for all 5 axes."""
    axes = []
    for i in range(_RADAR_N_AXES):
        angle = _axis_angle(i)
        x2, y2 = _polar_to_cartesian(_RADAR_MAX_R, angle)
        lx, ly = _polar_to_cartesian(_RADAR_LABEL_R, angle)

        # SVG text-anchor based on horizontal position
        if lx < _RADAR_CX - 8:
            anchor = "end"
        elif lx > _RADAR_CX + 8:
            anchor = "start"
        else:
            anchor = "middle"

        # Small vertical offset so label doesn't sit exactly on the polygon
        ly_adj = round(ly + (3.0 if ly > _RADAR_CY else -3.0), 2)

        axes.append({
            "x2":    f"{x2:.2f}",
            "y2":    f"{y2:.2f}",
            "lx":    f"{lx:.2f}",
            "ly":    f"{ly_adj:.2f}",
            "label": _RADAR_LABELS[i],
            "anchor": anchor,
        })
    return axes


def _normalise_for_radar(p: dict) -> list[float]:
    """
    Return 5 normalised [0, 1] values for a player:
    [kda_norm, win_rate_norm, consistency_norm, match_freq_norm, score_norm]
    """
    kda_n   = min(p["kda"],            _KDA_CAP)   / _KDA_CAP
    wr_n    = min(p["win_rate"],       100.0)       / 100.0
    # Consistency: use consistency_index if set; otherwise proxy via games_analyzed
    cons_n  = (p["consistency_index"] / 100.0) if p["consistency_index"] > 0 \
              else min(p["games_analyzed"], _GAMES_CAP) / _GAMES_CAP
    mf_n    = min(p["games_analyzed"], _GAMES_CAP) / _GAMES_CAP
    score_n = min(p["gameradar_score"], 10.0) / 10.0
    return [kda_n, wr_n, cons_n, mf_n, score_n]


def _compute_radar(players: list[dict]) -> dict:
    """
    Build the complete radar chart data object to inject into the Jinja2 context.

    Returns a dict with pre-computed SVG strings:
        grid_25, grid_50, grid_75, grid_100 — background pentagons
        axes                                — axis line/label descriptors
        top1_poly, avg_poly                 — data polygons
        top1_dots, avg_dots                 — vertex dot coordinates
        top1_name                           — player name for legend
    """
    axes = _build_axes()

    # Top 1 player
    top1       = players[0]
    top1_vals  = _normalise_for_radar(top1)
    top1_pts   = _polygon_points(top1_vals)
    top1_dots  = []
    for i, v in enumerate(top1_vals):
        x, y = _polar_to_cartesian(_RADAR_MAX_R * max(0.0, min(1.0, v)), _axis_angle(i))
        top1_dots.append({"x": f"{x:.2f}", "y": f"{y:.2f}"})

    # Region average
    n_players = len(players)
    avg_vals  = [
        sum(_normalise_for_radar(p)[i] for p in players) / n_players
        for i in range(_RADAR_N_AXES)
    ]
    avg_pts  = _polygon_points(avg_vals)
    avg_dots = []
    for i, v in enumerate(avg_vals):
        x, y = _polar_to_cartesian(_RADAR_MAX_R * max(0.0, min(1.0, v)), _axis_angle(i))
        avg_dots.append({"x": f"{x:.2f}", "y": f"{y:.2f}"})

    return {
        "grid_25":   _grid_polygon(0.25),
        "grid_50":   _grid_polygon(0.50),
        "grid_75":   _grid_polygon(0.75),
        "grid_100":  _grid_polygon(1.00),
        "axes":      axes,
        "top1_poly": top1_pts,
        "avg_poly":  avg_pts,
        "top1_dots": top1_dots,
        "avg_dots":  avg_dots,
        "top1_name": top1["nickname"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — MARKET TRENDS (default / example data)
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_MARKET_TRENDS: list[dict[str, str]] = [
    {
        "source":        "Wanplus",
        "title":         "LPL mid-laners dominate solo queue KDA rankings ahead of playoffs",
        "summary":       (
            "Analysis from Wanplus data shows LPL mid-laners averaging 5.8+ KDA "
            "over the past two weeks. Knight (TES) maintains position as the most "
            "consistent performer. Forum discussion highlights aggressive early-game "
            "adaptations and increased roaming in the current meta."
        ),
        "original_lang": "Mandarin Chinese (zh-CN)",
        "date":          "Apr 17, 2026",
    },
    {
        "source":        "TEC",
        "title":         "Indian Challenger players show rapid development in macro play",
        "summary":       (
            "TEC India community reports that domestic Challenger players are closing "
            "the gap with established Asian regions. Win rates in high-Elo India queue "
            "increased by 3.2% over the past month, driven by coordinated team "
            "compositions and improved objective control."
        ),
        "original_lang": "Hindi (hi) / English",
        "date":          "Apr 15, 2026",
    },
    {
        "source":        "Wanplus",
        "title":         "Post-patch ADC stats surge — JackeyLove leads iG recovery",
        "summary":       (
            "Post-patch 14.7 data from Wanplus confirms JackeyLove (iG) posting "
            "improved laning phase numbers. Gold per minute up 4.2% vs prior period. "
            "Forum analysts note that Infinity Edge buffs disproportionately benefit "
            "Crit ADC players in the Chinese ladder meta."
        ),
        "original_lang": "Mandarin Chinese (zh-CN)",
        "date":          "Apr 12, 2026",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — CONTEXT BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_context(
    players: list[dict],
    region: str,
    report_month: str,
    top_n: int,
    market_trends: list[dict],
) -> dict[str, Any]:
    """Assemble the full Jinja2 template context."""
    top_players = players[:top_n]
    rising_stars = players[:3]

    # Region averages
    n = len(top_players)
    region_avg = {
        "kda":            round(sum(p["kda"]            for p in top_players) / n, 2),
        "win_rate":       round(sum(p["win_rate"]       for p in top_players) / n, 1),
        "games_analyzed": round(sum(p["games_analyzed"] for p in top_players) / n, 0),
        "gameradar_score":round(sum(p["gameradar_score"]for p in top_players) / n, 2),
    }

    return {
        # Header
        "report_date":    datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "report_period":  report_month,
        "report_region":  region,
        # Summary
        "region_avg":     region_avg,
        # Tables
        "top_players":    top_players,
        "rising_stars":   rising_stars,
        # Trends
        "market_trends":  market_trends,
        # Radar chart
        "radar":          _compute_radar(top_players),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — RENDER & GENERATE PDF
# ══════════════════════════════════════════════════════════════════════════════

def _open_pdf(path: pathlib.Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        logger.warning(f"Could not open PDF automatically: {exc}")


def generate(
    output_path: pathlib.Path,
    *,
    region:       str = "Asia Pacific",
    report_month: str | None = None,
    data_source:  str = "master",
    top_n:        int = 10,
    auto_open:    bool = True,
    html_only:    bool = False,
    market_trends: list[dict] | None = None,
) -> None:
    """
    Full pipeline:
        load → normalise → score/rank → build radar → render Jinja2 → WeasyPrint PDF

    Parameters
    ----------
    output_path   : Destination PDF path.
    region        : Human-readable region label for the report header.
    report_month  : e.g. "April 2026". Defaults to current month.
    data_source   : 'master' (master_rookie.json) or 'silver' (silver_data.json).
    top_n         : Number of players to include in the ranking table (max 10).
    auto_open     : Open the PDF after generation.
    html_only     : Render HTML only (skip WeasyPrint).
    market_trends : Override the default market trend cards.
    """
    if not JINJA2_OK:
        sys.exit(1)

    report_month = report_month or datetime.now().strftime("%B %Y")
    top_n        = min(max(top_n, 3), 10)
    trends       = market_trends or DEFAULT_MARKET_TRENDS

    logger.info("=" * 62)
    logger.info("  GameRadar AI — Rookie Report Generator")
    logger.info(f"  Region   : {region}")
    logger.info(f"  Period   : {report_month}")
    logger.info(f"  Top N    : {top_n}")
    logger.info(f"  Source   : {data_source}")
    logger.info(f"  Output   : {output_path}")
    logger.info("=" * 62)

    # ── 1. Load & normalise ────────────────────────────────────────────────
    raw_players = _load_players(data_source)
    players     = [_normalise_player(p) for p in raw_players]

    # ── 2. Score & rank ────────────────────────────────────────────────────
    players = _score_and_rank(players)
    logger.info(f"Scored {len(players)} players. Top: {players[0]['nickname']} "
                f"({players[0]['gameradar_score']:.4f})")

    # ── 3. Build Jinja2 context ────────────────────────────────────────────
    context = _build_context(players, region, report_month, top_n, trends)

    # ── 4. Render HTML ─────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template      = env.get_template(TEMPLATE_FILE)
    rendered_html = template.render(**context)

    # Dump HTML preview
    html_out = output_path.with_suffix(".html")
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(rendered_html, encoding="utf-8")
    logger.info(f"HTML preview: {html_out}")

    if html_only or not WEASY_OK:
        if not WEASY_OK:
            logger.warning(
                "WeasyPrint unavailable — HTML only.\n"
                "  Install: pip install weasyprint==62.3\n"
                "  Windows: GTK runtime also required — "
                "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
            )
        logger.success(f"HTML generated: {html_out}")
        return

    # ── 5. WeasyPrint → PDF ────────────────────────────────────────────────
    logger.info("Rendering PDF with WeasyPrint …")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    WeasyHTML(
        string=rendered_html,
        base_url=str(TEMPLATE_DIR),   # resolves rookie_report.css
    ).write_pdf(
        str(output_path),
        presentational_hints=True,
    )

    size_bytes = output_path.stat().st_size
    size_kb    = size_bytes // 1024
    size_mb    = size_bytes / 1_048_576

    # DoD #3 — aesthetics: PDF must stay below 2 MB to avoid spam filters
    _DOD_PDF_MAX_MB = 2.0
    if size_mb > _DOD_PDF_MAX_MB:
        logger.warning(
            f"DoD #3 BREACH: PDF is {size_mb:.2f} MB "
            f"(limit {_DOD_PDF_MAX_MB} MB) — {output_path}\n"
            "  Tip: reduce image embeds or use font subsetting."
        )
    else:
        logger.success(
            f"PDF generated: {output_path}  ({size_kb} KB)  "
            f"\u2713 DoD #3 <{_DOD_PDF_MAX_MB} MB"
        )

    if auto_open:
        _open_pdf(output_path)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(
        description="GameRadar AI — Rookie Plan PDF Report Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_rookie_report.py
  python generate_rookie_report.py --output reports/rookie_april_2026.pdf
  python generate_rookie_report.py --region "Korea LCK" --month "April 2026"
  python generate_rookie_report.py --source silver --top 5
  python generate_rookie_report.py --html-only --no-open
""",
    )

    parser.add_argument(
        "--output", "-o",
        default=str(REPORTS_DIR / f"rookie_{datetime.now().strftime('%Y-%m')}.pdf"),
        help="Output PDF path (default: reports/rookie_YYYY-MM.pdf)",
    )
    parser.add_argument(
        "--region", "-r",
        default="Asia Pacific",
        help="Region label shown in the report header (default: 'Asia Pacific')",
    )
    parser.add_argument(
        "--month", "-m",
        default=None,
        help="Reporting period, e.g. 'April 2026' (default: current month)",
    )
    parser.add_argument(
        "--source", "-s",
        choices=["master", "silver"],
        default="master",
        help="Data source: 'master' (master_rookie.json) or 'silver' (default: master)",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=10,
        metavar="N",
        help="Number of players in ranking table, 3–10 (default: 10)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Generate HTML preview only, skip WeasyPrint PDF rendering",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the PDF automatically after generation",
    )

    args = parser.parse_args()

    # Configure loguru
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

    generate(
        output_path  = pathlib.Path(args.output),
        region       = args.region,
        report_month = args.month,
        data_source  = args.source,
        top_n        = args.top,
        auto_open    = not args.no_open,
        html_only    = args.html_only,
    )
