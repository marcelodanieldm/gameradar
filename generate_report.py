"""
generate_report.py — GameRadar AI · PDF Scouting Report Generator
=================================================================

Lee silver_data.json, renderiza la plantilla Jinja2 y genera el PDF
mensual del plan Rookie usando WeasyPrint.

Requiere:
    pip install weasyprint==62.3 jinja2==3.1.4

Uso:
    python generate_report.py
    python generate_report.py --output reports/scouting_abril_2026.pdf
    python generate_report.py --month "April 2026" --week 3
    python generate_report.py --top 5 --no-open
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
from typing import Any, Dict, List, Optional

from loguru import logger

# ──────────────────────────────────────────────────────────────────────────────
# Dependencias opcionales con mensajes útiles
# ──────────────────────────────────────────────────────────────────────────────
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_OK = True
except ImportError:
    JINJA2_OK = False
    logger.error("Jinja2 no instalado. Ejecuta: pip install jinja2==3.1.4")

try:
    from weasyprint import HTML as WeasyHTML
    from weasyprint import CSS
    WEASY_OK = True
except ImportError:
    WEASY_OK = False
    logger.error(
        "WeasyPrint no instalado. Ejecuta:\n"
        "  pip install weasyprint==62.3\n"
        "  (Requiere GTK en Windows — ver https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR      = pathlib.Path(__file__).parent
SILVER_PATH   = BASE_DIR / "silver" / "silver_data.json"
TEMPLATE_DIR  = BASE_DIR / "templates"
TEMPLATE_FILE = "scouting_report.html"
REPORTS_DIR   = BASE_DIR / "reports"

# ──────────────────────────────────────────────────────────────────────────────
# Glosario de términos traducidos — ampliar según necesidad
# ──────────────────────────────────────────────────────────────────────────────
GLOSSARY = [
    # Roles
    {
        "english":    "Mid Laner",
        "original":   "中单 (Zhōng dān) / 미드 라이너",
        "definition": "Player controlling the central lane. Requires high KDA and map pressure. Dominant position in LPL and LCK.",
    },
    {
        "english":    "ADC / Marksman",
        "original":   "射手 (Shèshǒu) / 원거리 딜러",
        "definition": "Attack Damage Carry. Primary ranged DPS in bot lane. Win Rate is the most predictive metric for ADC performance.",
    },
    {
        "english":    "Jungler",
        "original":   "打野 (Dǎ yě) / 정글러",
        "definition": "Neutral objectives specialist. Consistency Index reflects objective control over a season.",
    },
    {
        "english":    "Support",
        "original":   "辅助 (Fǔzhù) / 서포터",
        "definition": "Vision and peel specialist. High Games_Analyzed indicates tournament regularity and professional experience.",
    },
    {
        "english":    "Top Laner",
        "original":   "上单 (Shàng dān) / 탑 라이너",
        "definition": "Isolated solo laner. Valued for split-push and carry potential in Asian meta.",
    },
    {
        "english":    "Challenger",
        "original":   "挑战者 / 챌린저 / チャレンジャー",
        "definition": "Highest ladder rank in all servers. Prerequisite tier for professional team tryouts in Korea and China.",
    },
    {
        "english":    "KDA Ratio",
        "original":   "击杀死亡助攻 / 킬뎃어시",
        "definition": "(Kills + Assists) ÷ Deaths. Capped at 15 for normalisation. Score weight: 30%.",
    },
    {
        "english":    "GameRadar Score",
        "original":   "综合评分 / 종합 점수",
        "definition": "Proprietary index [0–10]. Formula: (KDA×0.3)+(WinRate×0.4)+(Consistency×0.3). Source-agnostic and cross-region comparable.",
    },
    {
        "english":    "LPL",
        "original":   "英雄联盟职业联赛",
        "definition": "League of Legends Pro League — China's top-tier LoL competition. Players sourced from Wanplus and PentaQ.",
    },
    {
        "english":    "LCK",
        "original":   "리그 오브 레전드 챔피언스 코리아",
        "definition": "League of Legends Champions Korea. Data sourced from Dak.gg and OP.GG KR.",
    },
    {
        "english":    "Consistency Index",
        "original":   "稳定性指数 / 일관성 지수",
        "definition": "Derived metric [0–100] based on consistency_score, games_analyzed, or tournament_participations. Score weight: 30%.",
    },
    {
        "english":    "Smurf Account",
        "original":   "小号 (Xiǎo hào) / 스머프",
        "definition": "Secondary account used by professional players. Detected via abnormal KDA+WinRate outliers in ladder data.",
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_silver(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        logger.error(f"silver_data.json no encontrado: {path}")
        logger.error("Ejecuta primero:  python bronze_to_silver.py")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _get_week_number() -> int:
    """Devuelve la semana del mes actual (1-4)."""
    day = datetime.now().day
    return math.ceil(day / 7)


def _open_pdf(path: pathlib.Path) -> None:
    """Abre el PDF con el visor del sistema."""
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        logger.warning(f"No se pudo abrir el PDF automáticamente: {exc}")


def _build_template_context(
    silver: Dict[str, Any],
    top_n: int,
    report_month: str,
    report_week: int,
) -> Dict[str, Any]:
    """Construye el contexto completo para el template Jinja2."""
    meta        = silver.get("_meta", {})
    all_players = silver.get("players", [])

    # Rellenar campos que podrían faltar
    for p in all_players:
        p.setdefault("KDA",               0.0)
        p.setdefault("Win_Rate_Pct",       0.0)
        p.setdefault("Consistency_Index",  0.0)
        p.setdefault("Games_Analyzed",     0)
        p.setdefault("Calculated_Score",   0.0)
        p.setdefault("Translated_Role",    "")
        p.setdefault("Real_Name",          "")
        p.setdefault("Team",               "")
        p.setdefault("Region",             "Global")
        p.setdefault("Game",               "LOL")
        p.setdefault("Data_Source",        "")
        p.setdefault("Bronze_Date",        "")

    top5        = all_players[:top_n]
    data_sources = sorted({p["Data_Source"] for p in all_players if p.get("Data_Source")})

    return {
        # Header
        "report_month":           report_month,
        "report_week":            report_week,
        "generated_at":           datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        # Summary stats
        "total_players_scouted":  meta.get("total_records", len(all_players)),
        "regions_covered":        meta.get("sources_covered", len(data_sources)),
        "avg_score":              f"{meta.get('avg_gameradar_score', 0):.2f}",
        "translations_applied":   meta.get("translations_applied", 0),
        # Tables
        "top5":                   top5,
        "all_players":            all_players,
        # Glossary
        "glossary":               GLOSSARY,
        # Sources strip
        "data_sources":           data_sources,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def generate_pdf(
    output_path: pathlib.Path,
    top_n: int = 5,
    report_month: Optional[str] = None,
    report_week: Optional[int] = None,
    auto_open: bool = True,
    html_only: bool = False,
) -> None:
    if not JINJA2_OK:
        sys.exit(1)

    now           = datetime.now()
    report_month  = report_month or now.strftime("%B %Y")
    report_week   = report_week  or _get_week_number()

    logger.info("=" * 60)
    logger.info("📄  GameRadar AI — PDF Report Generator")
    logger.info(f"   Month    : {report_month}")
    logger.info(f"   Week     : {report_week}")
    logger.info(f"   Top N    : {top_n}")
    logger.info(f"   Output   : {output_path}")
    logger.info("=" * 60)

    # ── 1. Load silver ──────────────────────────────────────────────────────
    silver  = _load_silver(SILVER_PATH)
    context = _build_template_context(silver, top_n, report_month, report_week)
    logger.info(f"   Loaded {len(silver.get('players',[]))} players from silver.")

    # ── 2. Render HTML with Jinja2 ──────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    # Custom filters for math operations used in the radar chart
    env.filters["sin"] = math.sin
    env.filters["cos"] = math.cos
    env.filters["min"] = min

    template     = env.get_template(TEMPLATE_FILE)
    rendered_html = template.render(**context)

    # Optional: dump HTML for inspection
    html_out = output_path.with_suffix(".html")
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(rendered_html, encoding="utf-8")
    logger.info(f"   HTML preview: {html_out}")

    if html_only:
        logger.success(f"✅  HTML only mode. Open {html_out} in a browser.")
        return

    # ── 3. WeasyPrint → PDF ─────────────────────────────────────────────────
    if not WEASY_OK:
        logger.warning(
            "⚠️  WeasyPrint no disponible — generando sólo HTML.\n"
            "   Instala GTK + weasyprint para exportar PDF:\n"
            "   https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
        )
        logger.success(f"✅  HTML generado: {html_out}")
        return

    logger.info("⚙️   Renderizando PDF con WeasyPrint…")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    WeasyHTML(string=rendered_html, base_url=str(TEMPLATE_DIR)).write_pdf(
        str(output_path),
        presentational_hints=True,
    )

    size_kb = output_path.stat().st_size // 1024
    logger.success(f"✅  PDF generado: {output_path}  ({size_kb} KB)")

    if auto_open:
        _open_pdf(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GameRadar AI — PDF Scouting Report Generator (WeasyPrint)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python generate_report.py
  python generate_report.py --month "April 2026" --week 3
  python generate_report.py --output reports/custom.pdf --top 10
  python generate_report.py --html-only          # sin WeasyPrint (preview)
  python generate_report.py --no-open            # no abrir al terminar
        """,
    )
    parser.add_argument(
        "--output", "-o",
        type=pathlib.Path,
        default=None,
        help="Ruta del PDF de salida (default: reports/scouting_<month>.pdf)",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help='Mes del reporte, e.g. "April 2026" (default: mes actual)',
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        metavar="1-4",
        help="Semana del mes (default: semana actual)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Número de jugadores en el Top (default: 5)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Solo generar HTML (sin WeasyPrint, útil para preview)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="No abrir el PDF automáticamente al terminar",
    )

    args = parser.parse_args()

    # Default output filename
    now = datetime.now()
    month_slug = (args.month or now.strftime("%B_%Y")).replace(" ", "_").lower()
    output = args.output or REPORTS_DIR / f"scouting_{month_slug}.pdf"

    generate_pdf(
        output_path  = output,
        top_n        = args.top,
        report_month = args.month,
        report_week  = args.week,
        auto_open    = not args.no_open,
        html_only    = args.html_only,
    )
