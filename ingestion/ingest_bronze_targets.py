"""
Bronze Ingestion — Asia Full Pipeline
======================================

Script diseñado para ejecutarse en GitHub Actions cada 12 horas.
Cubre las 11 fuentes del ecosistema asiático de e-sports:

  Corea/Japón : Dak.gg (Playwright), OP.GG (API), ZETA Division,
                DetonatioN, Game-i.daa.jp
  China       : Wanplus (API), PentaQ
  India/SEA   : The Esports Club, VRL Vyper, GosuGamers SEA
  Global      : Liquipedia (API backup)

Uso:
    python ingest_bronze_targets.py
    python ingest_bronze_targets.py --sources opgg_kr pentaq liquipedia
    python ingest_bronze_targets.py --dry-run

Variables de entorno opcionales:
    RIOT_API_KEY, STEAM_API_KEY
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

# ──────────────────────────────────────────────────────────────
# Imports del proyecto
# ──────────────────────────────────────────────────────────────
from scraping.strategic_adapters import AdvancedHeaderRotator, RegionProfile, ExponentialBackoffHandler
from scraping.asia_adapters import (
    OPGGAdapter,
    ZetaDivisionAdapter,
    DetonatioNAdapter,
    GameiJapanAdapter,
    PentaQAdapter,
    VRLVyperAdapter,
    GosuGamersSEAAdapter,
    LiquipediaAdapter,
)

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
BRONZE_DIR = Path(__file__).parent.parent / "bronze"
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

OPGG_KR_TARGETS = [
    {"id": "Faker",      "game": "lol"},
    {"id": "Chovy",      "game": "lol"},
    {"id": "ShowMaker",  "game": "lol"},
    {"id": "Keria",      "game": "lol"},
    {"id": "Ruler",      "game": "lol"},
]

OPGG_JP_TARGETS = [
    {"id": "Evi",        "game": "lol"},
    {"id": "Yutapon",   "game": "lol"},
    {"id": "Steal",      "game": "lol"},
]

ZETA_TARGETS = [
    {"id": "TENNN",     "game": "valorant"},
    {"id": "Laz",       "game": "valorant"},
    {"id": "dep",       "game": "valorant"},
]

DETONATION_TARGETS = [
    {"id": "Evi",        "game": "lol"},
    {"id": "Peace",      "game": "lol"},
    {"id": "Harp",       "game": "lol"},
]

GAMEI_JAPAN_TARGETS = [
    {"id": "Faker",      "game": "lol"},
    {"id": "Laz",       "game": "valorant"},
]

PENTAQ_TARGETS = [
    {"id": "JackeyLove", "game": "lol"},
    {"id": "Knight",     "game": "lol"},
    {"id": "Uzi",        "game": "lol"},
]

VRL_VYPER_TARGETS = [
    {"id": "Shadow",     "game": "valorant"},
    {"id": "Bazzi",      "game": "valorant"},
    {"id": "K1nG",       "game": "valorant"},
]

GOSUGAMERS_TARGETS = [
    {"id": "Whitemon",   "game": "dota2"},
    {"id": "Miracle-",   "game": "dota2"},
    {"id": "MSS",        "game": "dota2"},
]

LIQUIPEDIA_TARGETS = [
    {"id": "Faker",      "game": "lol"},
    {"id": "JackeyLove", "game": "lol"},
    {"id": "Yutapon",   "game": "lol"},
    {"id": "Shadow",     "game": "lol"},
    {"id": "Whitemon",   "game": "dota2"},
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
# Scraper genérico para adapters httpx de AsiaAdapters
# ──────────────────────────────────────────────

async def scrape_via_adapter(
    targets: List[Dict[str, str]],
    adapter,
    source_name: str,
) -> List[Dict[str, Any]]:
    """
    Función genérica para adapters que implementan fetch_player().
    Reutilizable para todos los adapters de AsiaAdapters.
    """
    results: List[Dict[str, Any]] = []
    for target in targets:
        player_id = target["id"]
        game      = target.get("game", "lol")
        try:
            raw = await adapter.fetch_player(player_id, game=game)
            if raw:
                results.append(sanitize_record(raw, source_name))
                logger.info(f"  ✅ {source_name} — {player_id}")
            else:
                logger.warning(f"  ⚠️  {source_name} — {player_id}: sin datos")
                results.append(sanitize_record(
                    _skeleton(player_id, "XX", "UNKNOWN", source_name), source_name
                ))
        except Exception as e:
            logger.warning(f"  ⚠️  {source_name} error para {player_id}: {e}")
            results.append(sanitize_record(
                _skeleton(player_id, "XX", "UNKNOWN", source_name), source_name
            ))
    return results

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


def _build_summary(source_results: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Genera resumen de la ejecución para logging."""
    def count_full(records: List[Dict]) -> int:
        return sum(1 for r in records if not r.get("_partial"))

    breakdown = {
        src: {"total": len(recs), "with_data": count_full(recs)}
        for src, recs in source_results.items()
    }
    return {
        "run_ts":    RUN_TS,
        "date":      TODAY,
        "sources":   breakdown,
        "total_records": sum(len(r) for r in source_results.values()),
        "total_with_data": sum(v["with_data"] for v in breakdown.values()),
    }


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

ALL_SOURCES = [
    "wanplus", "dakgg", "tec_india",
    "opgg_kr", "opgg_jp",
    "zeta_division", "detonation", "gamei_japan",
    "pentaq",
    "vrl_vyper", "gosugamers_sea",
    "liquipedia",
]


async def main(sources: Optional[List[str]] = None, dry_run: bool = False) -> None:
    sources = sources or ALL_SOURCES

    logger.info("=" * 70)
    logger.info(f"🚀  GameRadar Bronze Ingestion — {TODAY}")
    logger.info(f"   Fuentes ({len(sources)}): {', '.join(sources)}")
    logger.info(f"   Dry-run: {dry_run}")
    logger.info("=" * 70)

    source_results: Dict[str, List[Dict]] = {}

    async with httpx.AsyncClient(
        timeout=30,
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=3),
        verify=False,
        http2=True,
    ) as http_client:

        if "wanplus" in sources:
            logger.info("\n📡  Scraping Wanplus (China / LPL)…")
            source_results["wanplus"] = await scrape_wanplus(WANPLUS_TARGETS, http_client)

        if "tec_india" in sources:
            logger.info("\n📡  Scraping The Esports Club (India)…")
            source_results["tec_india"] = await scrape_tec_india(TEC_INDIA_TARGETS, http_client)

        if "opgg_kr" in sources:
            logger.info("\n📡  Scraping OP.GG Korea…")
            adapter = OPGGAdapter(client=http_client, region="kr")
            source_results["opgg_kr"] = await scrape_via_adapter(OPGG_KR_TARGETS, adapter, "opgg_kr")

        if "opgg_jp" in sources:
            logger.info("\n📡  Scraping OP.GG Japan…")
            adapter = OPGGAdapter(client=http_client, region="jp")
            source_results["opgg_jp"] = await scrape_via_adapter(OPGG_JP_TARGETS, adapter, "opgg_jp")

        if "zeta_division" in sources:
            logger.info("\n📡  Scraping ZETA Division (Japan)…")
            adapter = ZetaDivisionAdapter(client=http_client)
            source_results["zeta_division"] = await scrape_via_adapter(ZETA_TARGETS, adapter, "zeta_division")

        if "detonation" in sources:
            logger.info("\n📡  Scraping DetonatioN FocusMe (Japan)…")
            adapter = DetonatioNAdapter(client=http_client)
            source_results["detonation"] = await scrape_via_adapter(DETONATION_TARGETS, adapter, "detonation")

        if "gamei_japan" in sources:
            logger.info("\n📡  Scraping Game-i.daa.jp (Japan rankings)…")
            adapter = GameiJapanAdapter(client=http_client)
            source_results["gamei_japan"] = await scrape_via_adapter(GAMEI_JAPAN_TARGETS, adapter, "gamei_japan")

        if "pentaq" in sources:
            logger.info("\n📡  Scraping PentaQ (China analysis)…")
            adapter = PentaQAdapter(client=http_client)
            source_results["pentaq"] = await scrape_via_adapter(PENTAQ_TARGETS, adapter, "pentaq")

        if "vrl_vyper" in sources:
            logger.info("\n📡  Scraping VRL Vyper (India / Valorant)…")
            adapter = VRLVyperAdapter(client=http_client)
            source_results["vrl_vyper"] = await scrape_via_adapter(VRL_VYPER_TARGETS, adapter, "vrl_vyper")

        if "gosugamers_sea" in sources:
            logger.info("\n📡  Scraping GosuGamers SEA (Dota2/ML)…")
            adapter = GosuGamersSEAAdapter(client=http_client)
            source_results["gosugamers_sea"] = await scrape_via_adapter(GOSUGAMERS_TARGETS, adapter, "gosugamers_sea")

        if "liquipedia" in sources:
            logger.info("\n📡  Scraping Liquipedia (global backup)…")
            adapter = LiquipediaAdapter(client=http_client)
            source_results["liquipedia"] = await scrape_via_adapter(LIQUIPEDIA_TARGETS, adapter, "liquipedia")

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
                source_results["dakgg"] = await scrape_dakgg(DAKGG_TARGETS, browser)
                await browser.close()

    if not dry_run:
        for src, records in source_results.items():
            if records:
                save_bronze(records, src)
    else:
        logger.info("\n[DRY-RUN] No se escribieron archivos.")

    summary = _build_summary(source_results)
    summary_path = BRONZE_DIR / "logs" / f"summary_{TODAY}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("\n" + "=" * 70)
    logger.info("📊  RESUMEN FINAL")
    for src, info in summary["sources"].items():
        icon = "✅" if info["with_data"] > 0 else "⚠️ "
        logger.info(f"   {icon} {src:<20}: {info['with_data']}/{info['total']} con datos")
    logger.info(f"   Total registros: {summary['total_records']}")
    logger.info(f"   Con datos reales: {summary['total_with_data']}")
    logger.info("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GameRadar Bronze Ingestion")
    parser.add_argument(
        "--sources", nargs="+",
        choices=ALL_SOURCES,
        default=ALL_SOURCES,
        help="Fuentes a scrapear (por defecto: todas)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Ejecutar sin escribir archivos",
    )
    args = parser.parse_args()

    asyncio.run(main(sources=args.sources, dry_run=args.dry_run))
