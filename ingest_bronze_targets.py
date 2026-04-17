"""
Bronze Ingestion — Wanplus + Dak.gg + The Esports Club India
=============================================================

Script diseñado para ejecutarse en GitHub Actions cada 12 horas.
Extrae datos de las tres fuentes, los sanitiza y los guarda en
/bronze/<source>/<YYYY-MM-DD>.json con rotación de headers integrada.

Uso:
    python ingest_bronze_targets.py
    python ingest_bronze_targets.py --sources wanplus tec_india
    python ingest_bronze_targets.py --dry-run

Variables de entorno (opcionales — el script funciona sin ellas):
    SUPABASE_URL, SUPABASE_KEY
"""

import asyncio
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page

# ──────────────────────────────────────────────
# Importamos AdvancedHeaderRotator del proyecto
# ──────────────────────────────────────────────
from StrategicAdapters import AdvancedHeaderRotator, RegionProfile, ExponentialBackoffHandler

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
BRONZE_DIR = Path(__file__).parent / "bronze"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
RUN_TS = datetime.now(timezone.utc).isoformat()

# Jugadores objetivo por fuente (extensible vía env vars / JSON externo)
WANPLUS_TARGETS = [
    {"id": "JackeyLove", "game": "lol"},
    {"id": "Knight",     "game": "lol"},
    {"id": "Uzi",        "game": "lol"},
    {"id": "Ruler",      "game": "lol"},
    {"id": "Rookie",     "game": "lol"},
]

DAKGG_TARGETS = [
    {"id": "Faker",      "game": "lol"},
    {"id": "Chovy",      "game": "lol"},
    {"id": "ShowMaker",  "game": "lol"},
    {"id": "Keria",      "game": "lol"},
    {"id": "Zeus",       "game": "lol"},
]

TEC_INDIA_TARGETS = [
    {"id": "Shadow",     "game": "lol"},
    {"id": "Clutch",     "game": "lol"},
    {"id": "Awoken",     "game": "lol"},
    {"id": "KingXtreme", "game": "lol"},
]

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logger.remove()
logger.add(sys.stdout, level="INFO",
           format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}")
logger.add(BRONZE_DIR / "logs" / f"ingest_{TODAY}.log",
           rotation="50 MB", retention="14 days", level="DEBUG")


# ──────────────────────────────────────────────
# Sanitización
# ──────────────────────────────────────────────

def sanitize_string(value: Any) -> Optional[str]:
    """Elimina caracteres de control, trunca a 512 chars, devuelve None si vacío."""
    if value is None:
        return None
    text = str(value)
    # Eliminar caracteres de control (excepto newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = text.strip()
    return text[:512] if text else None


def sanitize_float(value: Any, lo: float = 0.0, hi: float = 100.0) -> Optional[float]:
    """Convierte a float y clipa al rango [lo, hi]. Devuelve None si inválido."""
    try:
        f = float(value)
        if f != f:  # NaN check
            return None
        return max(lo, min(hi, f))
    except (TypeError, ValueError):
        return None


def sanitize_int(value: Any, lo: int = 0, hi: int = 10_000) -> Optional[int]:
    """Convierte a int y clipa al rango [lo, hi]. Devuelve None si inválido."""
    try:
        return max(lo, min(hi, int(float(value))))
    except (TypeError, ValueError):
        return None


def sanitize_record(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Aplica sanitización completa a un registro crudo antes de persistirlo.
    Garantiza que todos los campos estén dentro de rangos válidos y sin
    datos malformados (previene injection en downstream JSON/SQL).
    """
    stats_raw = raw.get("stats") or {}

    record: Dict[str, Any] = {
        # Identificación
        "source":      source,
        "scraped_at":  RUN_TS,
        "date":        TODAY,
        # Datos de jugador
        "nickname":    sanitize_string(raw.get("nickname")),
        "real_name":   sanitize_string(raw.get("real_name")),
        "team":        sanitize_string(raw.get("team")),
        "role":        sanitize_string(raw.get("role")),
        "rank":        sanitize_string(raw.get("rank")),
        "country":     sanitize_string(raw.get("country")),
        "server":      sanitize_string(raw.get("server")),
        "profile_url": sanitize_string(raw.get("profile_url") or raw.get("raw_url")),
        "game":        sanitize_string(raw.get("game", "LOL")),
        # Stats normalizados
        "stats": {
            "win_rate":                 sanitize_float(stats_raw.get("win_rate"),         0.0, 100.0),
            "kda":                      sanitize_float(stats_raw.get("kda"),              0.0, 50.0),
            "games_analyzed":           sanitize_int(stats_raw.get("games_analyzed"),     0,   5_000),
            # Micro-metrics (China)
            "apm":                      sanitize_int(stats_raw.get("apm"),                0,   1_000),
            "gold_per_min":             sanitize_int(stats_raw.get("gold_per_min"),       0,   1_500),
            "damage_percent":           sanitize_float(stats_raw.get("damage_percent"),   0.0, 100.0),
            # Social metrics (India/Vietnam)
            "tournament_participations": sanitize_int(stats_raw.get("tournament_participations"), 0, 500),
            "consistency_score":        sanitize_float(stats_raw.get("consistency_score"), 0.0, 100.0),
            "community_rating":         sanitize_float(stats_raw.get("community_rating"),  0.0, 10.0),
        },
    }

    # Eliminar claves con valor None para mantener JSON limpio
    record["stats"] = {k: v for k, v in record["stats"].items() if v is not None}

    return record


# ──────────────────────────────────────────────
# Persistencia
# ──────────────────────────────────────────────

def save_bronze(records: List[Dict[str, Any]], source: str) -> Path:
    """
    Guarda registros en /bronze/<source>/<YYYY-MM-DD>.json.
    Si el archivo ya existe (ejecución del mismo día), hace merge por nickname.
    """
    dest_dir = BRONZE_DIR / source
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{TODAY}.json"

    existing: List[Dict[str, Any]] = []
    if dest_file.exists():
        try:
            existing = json.loads(dest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning(f"⚠️  {dest_file} corrupto — sobreescribiendo.")

    # Merge: nickname actúa como clave; el nuevo registro gana
    index = {r["nickname"]: r for r in existing if r.get("nickname")}
    for r in records:
        if r.get("nickname"):
            index[r["nickname"]] = r
        else:
            existing.append(r)  # registros sin nickname se acumulan

    merged = list(index.values()) + [r for r in existing if not r.get("nickname")]

    dest_file.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.success(f"💾 Guardado: {dest_file}  ({len(merged)} registros)")
    return dest_file


# ──────────────────────────────────────────────
# Scraper: Wanplus (httpx + HTML parsing ligero)
# ──────────────────────────────────────────────

async def scrape_wanplus(
    targets: List[Dict[str, str]],
    client: httpx.AsyncClient
) -> List[Dict[str, Any]]:
    """
    Scraper para Wanplus.com (LPL / China).
    Usa httpx con headers rotativos chinos.
    Wanplus renderiza parte del contenido server-side, por lo que intentamos
    primero la API interna JSON; si devuelve 403/captcha, devolvemos esqueleto.
    """
    results: List[Dict[str, Any]] = []

    for target in targets:
        player_id = target["id"]
        game      = target.get("game", "lol")

        await ExponentialBackoffHandler.delay(RegionProfile.CHINA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.CHINA)

        # Wanplus tiene endpoint de API interno (no documentado)
        api_url = f"https://www.wanplus.com/ajax/summoner/stats"
        params  = {"name": player_id, "gameType": "lol"}

        try:
            resp = await client.get(api_url, headers=headers, params=params,
                                    timeout=20, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

            player_node = data.get("data", {}).get("player") or {}

            raw = {
                "nickname":    player_node.get("summonerName") or player_id,
                "real_name":   player_node.get("realName"),
                "team":        player_node.get("teamName"),
                "role":        player_node.get("position"),
                "win_rate":    player_node.get("winRate"),
                "kda":         player_node.get("kda"),
                "apm":         player_node.get("apm"),
                "gold_per_min": player_node.get("goldPerMin"),
                "damage_percent": player_node.get("damagePercent"),
                "games_played": player_node.get("gamesPlayed"),
                "rank":        player_node.get("rank"),
                "server":      player_node.get("server", "Ionia"),
                "country":     "CN",
                "game":        "LOL",
                "raw_url":     f"https://www.wanplus.com/lol/player/{player_id}",
                "stats": {
                    "win_rate":      player_node.get("winRate"),
                    "kda":           player_node.get("kda"),
                    "games_analyzed": player_node.get("gamesPlayed"),
                    "apm":           player_node.get("apm"),
                    "gold_per_min":  player_node.get("goldPerMin"),
                    "damage_percent": player_node.get("damagePercent"),
                }
            }

            logger.info(f"  🇨🇳 Wanplus — {player_id}: {'datos' if player_node else 'sin datos (esqueleto)'}")

        except httpx.HTTPStatusError as e:
            logger.warning(f"  ⚠️  Wanplus HTTP {e.response.status_code} para {player_id}")
            raw = _skeleton(player_id, "CN", "Ionia", "wanplus")
        except Exception as e:
            logger.warning(f"  ⚠️  Wanplus error para {player_id}: {e}")
            raw = _skeleton(player_id, "CN", "Ionia", "wanplus")

        results.append(sanitize_record(raw, "wanplus"))

    return results


# ──────────────────────────────────────────────
# Scraper: Dak.gg (Playwright — JS pesado)
# ──────────────────────────────────────────────

async def scrape_dakgg(
    targets: List[Dict[str, str]],
    browser: Browser
) -> List[Dict[str, Any]]:
    """
    Scraper para Dak.gg (Korea).
    Usa Playwright porque el sitio es React/SSR con hydration.
    Estrategia: espera networkidle, luego extrae JSON embebido en __NEXT_DATA__.
    """
    results: List[Dict[str, Any]] = []

    for target in targets:
        player_id = target["id"]
        game      = target.get("game", "lol")

        await ExponentialBackoffHandler.delay(RegionProfile.KOREA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.KOREA)

        url = f"https://dak.gg/lol/players/{player_id}"

        context = await browser.new_context(
            user_agent=headers["User-Agent"],
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={
                "Accept-Language": headers["Accept-Language"],
                "Referer": "https://dak.gg/",
            },
        )
        page: Page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25_000)

            # Intentar extraer __NEXT_DATA__ (Next.js SSR payload)
            next_data_raw: str = await page.evaluate(
                "() => document.getElementById('__NEXT_DATA__')?.textContent || ''"
            )

            raw: Dict[str, Any] = {}

            if next_data_raw:
                try:
                    next_data = json.loads(next_data_raw)
                    # La estructura varía, buscamos el nodo de jugador
                    props   = next_data.get("props", {}).get("pageProps", {})
                    profile = (
                        props.get("player")
                        or props.get("summonerInfo")
                        or props.get("data", {}).get("player")
                        or {}
                    )
                    raw = {
                        "nickname":   profile.get("summonerName") or profile.get("name") or player_id,
                        "real_name":  profile.get("realName"),
                        "team":       profile.get("teamName") or profile.get("team"),
                        "rank":       (profile.get("tier") or "") + " " + (profile.get("division") or ""),
                        "win_rate":   profile.get("winRate") or profile.get("wins"),
                        "kda":        profile.get("kda"),
                        "games_played": profile.get("totalGames") or profile.get("games"),
                        "server":     "KR",
                        "country":    "KR",
                        "game":       "LOL",
                        "raw_url":    url,
                        "stats": {
                            "win_rate":       profile.get("winRate"),
                            "kda":            profile.get("kda"),
                            "games_analyzed": profile.get("totalGames"),
                        },
                    }
                    logger.info(f"  🇰🇷 Dak.gg — {player_id}: extraído desde __NEXT_DATA__")
                except json.JSONDecodeError:
                    logger.warning(f"  ⚠️  Dak.gg — {player_id}: __NEXT_DATA__ malformado")
                    raw = _skeleton(player_id, "KR", "KR", "dakgg")
            else:
                # Fallback: scraping DOM directo
                nick = await _safe_inner_text(page, ".summoner-name, [class*='summonerName'], h1")
                raw = _skeleton(player_id, "KR", "KR", "dakgg")
                if nick:
                    raw["nickname"] = nick
                logger.warning(f"  ⚠️  Dak.gg — {player_id}: sin __NEXT_DATA__, usando DOM fallback")

        except Exception as e:
            logger.warning(f"  ⚠️  Dak.gg error para {player_id}: {type(e).__name__}: {e}")
            raw = _skeleton(player_id, "KR", "KR", "dakgg")

        finally:
            await page.close()
            await context.close()

        results.append(sanitize_record(raw, "dakgg"))

    return results


# ──────────────────────────────────────────────
# Scraper: The Esports Club India (httpx + JSON API)
# ──────────────────────────────────────────────

async def scrape_tec_india(
    targets: List[Dict[str, str]],
    client: httpx.AsyncClient
) -> List[Dict[str, Any]]:
    """
    Scraper para The Esports Club (India).
    Usa httpx — TEC expone una API REST parcialmente pública.
    """
    results: List[Dict[str, Any]] = []

    for target in targets:
        player_id = target["id"]
        game      = target.get("game", "lol")

        await ExponentialBackoffHandler.delay(RegionProfile.INDIA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.INDIA)

        # Endpoint principal del perfil público
        url = f"https://www.theesportsclub.com/api/v1/player/{player_id}"

        try:
            resp = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            player_node = data.get("player") or data.get("data") or {}

            raw = {
                "nickname":                  player_node.get("username") or player_id,
                "real_name":                 player_node.get("real_name"),
                "team":                      player_node.get("team_name"),
                "role":                      player_node.get("role"),
                "rank":                      player_node.get("tier"),
                "server":                    "India",
                "country":                   "IN",
                "game":                      "LOL",
                "raw_url":                   player_node.get("profile_url"),
                "stats": {
                    "win_rate":                  player_node.get("win_rate"),
                    "kda":                       player_node.get("kda"),
                    "games_analyzed":            player_node.get("total_matches"),
                    "tournament_participations": player_node.get("tournaments_count"),
                    "consistency_score":         player_node.get("consistency"),
                    "community_rating":          player_node.get("rating"),
                },
            }
            logger.info(f"  🇮🇳 TEC India — {player_id}: datos recibidos")

        except httpx.HTTPStatusError as e:
            logger.warning(f"  ⚠️  TEC India HTTP {e.response.status_code} para {player_id}")
            raw = _skeleton(player_id, "IN", "India", "tec_india")
        except Exception as e:
            logger.warning(f"  ⚠️  TEC India error para {player_id}: {e}")
            raw = _skeleton(player_id, "IN", "India", "tec_india")

        results.append(sanitize_record(raw, "tec_india"))

    return results


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _skeleton(player_id: str, country: str, server: str, source: str) -> Dict[str, Any]:
    """Registro mínimo cuando el scraper no obtiene datos."""
    return {
        "nickname": player_id,
        "country":  country,
        "server":   server,
        "game":     "LOL",
        "raw_url":  None,
        "stats":    {},
        "_partial": True,   # flag para filtrado downstream
    }


async def _safe_inner_text(page: Page, selector: str) -> Optional[str]:
    """Devuelve innerText del primer selector que coincida, o None si falla."""
    for sel in selector.split(","):
        try:
            el = await page.query_selector(sel.strip())
            if el:
                return await el.inner_text()
        except Exception:
            continue
    return None


def _build_summary(
    wanplus_records: List[Dict],
    dakgg_records: List[Dict],
    tec_records: List[Dict],
) -> Dict[str, Any]:
    """Genera resumen de la ejecución para logging."""
    def count_full(records: List[Dict]) -> int:
        return sum(1 for r in records if not r.get("_partial"))

    return {
        "run_ts":    RUN_TS,
        "date":      TODAY,
        "wanplus":  {"total": len(wanplus_records),  "with_data": count_full(wanplus_records)},
        "dakgg":    {"total": len(dakgg_records),     "with_data": count_full(dakgg_records)},
        "tec_india":{"total": len(tec_records),       "with_data": count_full(tec_records)},
    }


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

async def main(sources: Optional[List[str]] = None, dry_run: bool = False) -> None:
    sources = sources or ["wanplus", "dakgg", "tec_india"]

    logger.info("=" * 60)
    logger.info(f"🚀  GameRadar Bronze Ingestion — {TODAY}")
    logger.info(f"   Fuentes: {', '.join(sources)}")
    logger.info(f"   Dry-run: {dry_run}")
    logger.info("=" * 60)

    wanplus_records: List[Dict] = []
    dakgg_records:   List[Dict] = []
    tec_records:     List[Dict] = []

    async with httpx.AsyncClient(
        timeout=30,
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=3),
        verify=False,       # algunos sitios usan certs auto-firmados
        http2=True,
    ) as http_client:

        # ── Wanplus (httpx) ──────────────────────────────
        if "wanplus" in sources:
            logger.info("\n📡  Scraping Wanplus (China / LPL)…")
            wanplus_records = await scrape_wanplus(WANPLUS_TARGETS, http_client)

        # ── TEC India (httpx) ────────────────────────────
        if "tec_india" in sources:
            logger.info("\n📡  Scraping The Esports Club (India)…")
            tec_records = await scrape_tec_india(TEC_INDIA_TARGETS, http_client)

        # ── Dak.gg (Playwright) ──────────────────────────
        if "dakgg" in sources:
            logger.info("\n📡  Scraping Dak.gg (Korea / Playwright)…")
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ],
                )
                dakgg_records = await scrape_dakgg(DAKGG_TARGETS, browser)
                await browser.close()

    # ── Persistencia ─────────────────────────────────────
    if not dry_run:
        if wanplus_records:
            save_bronze(wanplus_records, "wanplus")
        if dakgg_records:
            save_bronze(dakgg_records, "dakgg")
        if tec_records:
            save_bronze(tec_records, "tec_india")
    else:
        logger.info("\n[DRY-RUN] No se escribieron archivos.")

    # ── Resumen ───────────────────────────────────────────
    summary = _build_summary(wanplus_records, dakgg_records, tec_records)
    summary_path = BRONZE_DIR / "logs" / f"summary_{TODAY}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("\n" + "=" * 60)
    logger.info("📊  RESUMEN")
    logger.info(f"   Wanplus  : {summary['wanplus']['with_data']}/{summary['wanplus']['total']} con datos")
    logger.info(f"   Dak.gg   : {summary['dakgg']['with_data']}/{summary['dakgg']['total']} con datos")
    logger.info(f"   TEC India: {summary['tec_india']['with_data']}/{summary['tec_india']['total']} con datos")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GameRadar Bronze Ingestion")
    parser.add_argument(
        "--sources", nargs="+",
        choices=["wanplus", "dakgg", "tec_india"],
        default=["wanplus", "dakgg", "tec_india"],
        help="Fuentes a scrapear",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Ejecutar sin escribir archivos",
    )
    args = parser.parse_args()

    asyncio.run(main(sources=args.sources, dry_run=args.dry_run))
