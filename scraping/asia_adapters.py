"""
AsiaAdapters — Adaptadores adicionales para mercados asiáticos
==============================================================

Módulo complementario a StrategicAdapters.py.
Implementa los conectores que faltan para cubrir el ecosistema
completo de e-sports en Asia Oriental, China, India y SEA.

Fuentes implementadas:
  KR/JP  — OPGGAdapter, ZetaDivisionAdapter, DetonatioNAdapter, GameiJapanAdapter
  China  — PentaQAdapter
  SEA/IN — VRLVyperAdapter, GosuGamersSEAAdapter
  Global — LiquipediaAdapter (API backup para todas las regiones)

Diseño:
  • Todos heredan de BaseStrategicAdapter (StrategicAdapters.py)
  • Rotación de headers via AdvancedHeaderRotator por región
  • Backoff exponencial via ExponentialBackoffHandler
  • Salida normalizada al esquema Bronze (mismo formato que los adapters existentes)
  • Fallback a esqueleto si la fuente no responde

Author: GameRadar AI Data Engineering Team
"""

import asyncio
import random
import re
import urllib.parse
from abc import ABC
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from scraping.strategic_adapters import (
    AdvancedHeaderRotator,
    BaseStrategicAdapter,
    DataPriority,
    ExponentialBackoffHandler,
    RegionProfile,
    SourceMetadata,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_float(text: str) -> Optional[float]:
    """Extrae el primer número float/int de una cadena de texto."""
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else None


def _extract_percent(text: str) -> Optional[float]:
    """Extrae porcentaje (ej: '67.3%' → 67.3)."""
    m = re.search(r"(\d+\.?\d*)\s*%", text)
    return float(m.group(1)) if m else None


# ─────────────────────────────────────────────────────────────────────────────
# 1. OP.GG — Korea / Japan / Global (LOL / Valorant)
# ─────────────────────────────────────────────────────────────────────────────

class OPGGAdapter(BaseStrategicAdapter):
    """
    Adapter para OP.GG — el estándar de estadísticas de LoL en Corea.

    Usa la API interna no documentada de OP.GG. Soporta múltiples regiones
    (kr, jp, na, euw, etc.) y juegos (lol, valorant).

    Endpoint principal:
        GET https://op.gg/api/v1.0/internal/bypass/summoners/{region}/{name}/summary
    """

    _REGION_MAP = {
        "kr": RegionProfile.KOREA,
        "jp": RegionProfile.JAPAN,
    }

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        region: str = "kr",
    ) -> None:
        rp = self._REGION_MAP.get(region, RegionProfile.GLOBAL)
        metadata = SourceMetadata(
            source_name=f"opgg_{region}",
            region=rp,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://op.gg",
            requires_proxy=False,
            rate_limit_per_minute=60,
            reliability_score=0.92,
        )
        super().__init__(client, metadata)
        self.region = region

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        self.logger.info(f"🇰🇷 OP.GG [{self.region.upper()}] → {identifier} ({game})")

        rp = self._REGION_MAP.get(self.region, RegionProfile.GLOBAL)
        await ExponentialBackoffHandler.delay(rp)
        headers = AdvancedHeaderRotator.get_headers(rp)

        encoded = urllib.parse.quote(identifier)

        if game == "valorant":
            url = (
                f"https://op.gg/api/v1.0/internal/bypass/valorant"
                f"/summoners/{self.region}/{encoded}/summary"
            )
        else:
            # LoL — API interna no documentada
            url = (
                f"https://op.gg/api/v1.0/internal/bypass/summoners"
                f"/{self.region}/{encoded}/summary"
            )

        # OP.GG requiere Referer para no recibir 403
        headers["Referer"] = f"https://www.op.gg/summoners/{self.region}/{encoded}"
        headers["Accept"] = "application/json"

        try:
            resp = await self.client.get(url, headers=headers, timeout=20,
                                         follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

            summoner = data.get("data", {}).get("summoner", data.get("data", {}))
            lp_info  = data.get("data", {}).get("league_stats", [{}])
            solo     = next((r for r in lp_info if "RANKED_SOLO" in r.get("queue_info", {}).get("queue_type", "")), {})
            queue    = solo.get("queue_info", {})

            wins   = queue.get("win", 0) or 0
            losses = queue.get("lose", 0) or 0
            total  = wins + losses
            wr     = round(wins / total * 100, 2) if total else None

            raw = {
                "nickname":    summoner.get("name") or identifier,
                "real_name":   None,
                "team":        None,
                "role":        summoner.get("lane_stats", [{}])[0].get("lane") if summoner.get("lane_stats") else None,
                "rank":        f"{queue.get('tier', '')} {queue.get('division', '')}".strip() or None,
                "country":     "KR" if self.region == "kr" else "JP" if self.region == "jp" else self.region.upper(),
                "server":      self.region.upper(),
                "game":        game.upper(),
                "profile_url": f"https://www.op.gg/summoners/{self.region}/{encoded}",
                "stats": {
                    "win_rate":       wr,
                    "kda":            solo.get("kda"),
                    "games_analyzed": total,
                    "wins":           wins,
                    "losses":         losses,
                    "lp":             queue.get("league_points"),
                },
            }
            self._record_success()
            self.logger.success(f"✅ OP.GG [{self.region}] {identifier} — WR {wr}%")
            return self._normalize_to_bronze_schema(raw)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  OP.GG HTTP {e.response.status_code} → {identifier}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  OP.GG error → {identifier}: {e}")
            self._record_failure()
        return None

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "game":        raw.get("game", "LOL"),
            "country":     raw.get("country"),
            "server":      raw.get("server"),
            "rank":        raw.get("rank"),
            "role":        raw.get("role"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      self.metadata.source_name,
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. ZETA Division — Japan academy / Valorant team
# ─────────────────────────────────────────────────────────────────────────────

class ZetaDivisionAdapter(BaseStrategicAdapter):
    """
    Adapter para ZETA Division (Japón).

    Extrae el roster actual del equipo y métricas disponibles en el sitio oficial.
    Sirve como fuente de seguimiento de academias japonesas para Valorant y LoL.

    Base URL: https://zetadivision.com
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="zeta_division",
            region=RegionProfile.JAPAN,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://zetadivision.com",
            requires_proxy=False,
            rate_limit_per_minute=20,
            reliability_score=0.78,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "valorant",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un jugador por nombre en el roster de ZETA Division.
        Si identifier='__roster__' devuelve todos los miembros.
        """
        self.logger.info(f"🇯🇵 ZETA Division → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.JAPAN)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.JAPAN)

        # ZETA expone un JSON de roster en /api/members (o scraping HTML si no existe)
        roster_url = f"{self.metadata.base_url}/team"
        headers["Referer"] = self.metadata.base_url

        try:
            resp = await self.client.get(roster_url, headers=headers, timeout=15,
                                         follow_redirects=True)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")

            members: List[Dict[str, Any]] = []

            if "application/json" in content_type:
                data = resp.json()
                members = data.get("members", data.get("players", []))
            else:
                # Fallback: parseo ligero de HTML para extraer nombres
                html = resp.text
                found = re.findall(
                    r'(?:player|member)["\s]*:["\s]*([A-Za-z0-9_\-\.]+)',
                    html, re.IGNORECASE
                )
                members = [{"name": n} for n in set(found)]

            if identifier != "__roster__":
                members = [
                    m for m in members
                    if identifier.lower() in (m.get("name") or m.get("username") or "").lower()
                ]
                if not members:
                    self._record_failure()
                    return None

            # Normalizar primer resultado
            player = members[0] if members else {}
            raw = self._build_raw(player, identifier)
            self._record_success()
            return self._normalize_to_bronze_schema(raw)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  ZETA HTTP {e.response.status_code}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  ZETA error: {e}")
            self._record_failure()
        return None

    def _build_raw(self, player: Dict[str, Any], fallback_name: str) -> Dict[str, Any]:
        return {
            "nickname":    player.get("name") or player.get("username") or fallback_name,
            "real_name":   player.get("real_name") or player.get("realName"),
            "team":        "ZETA Division",
            "role":        player.get("role") or player.get("position"),
            "country":     "JP",
            "server":      "JP",
            "game":        "VALORANT",
            "profile_url": player.get("url") or player.get("twitter"),
            "stats":       {},
        }

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw["nickname"],
            "game":        raw.get("game", "VALORANT"),
            "country":     "JP",
            "server":      "JP",
            "team":        raw.get("team"),
            "role":        raw.get("role"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "zeta_division",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. DetonatioN FG — Japan's flagship org
# ─────────────────────────────────────────────────────────────────────────────

class DetonatioNAdapter(BaseStrategicAdapter):
    """
    Adapter para DetonatioN FocusMe (Japón).

    Extrae el roster oficial del sitio de DetonatioN, incluyendo la academia.
    Principal fuente de talento japonés para LoL, VALORANT y FPS mobile.

    Base URL: https://detonation.jp
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="detonation",
            region=RegionProfile.JAPAN,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://detonation.jp",
            requires_proxy=False,
            rate_limit_per_minute=20,
            reliability_score=0.80,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        self.logger.info(f"🇯🇵 DetonatioN → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.JAPAN)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.JAPAN)

        # Intentar endpoint JSON primero; caer en HTML si falla
        json_url  = f"{self.metadata.base_url}/api/members"
        html_url  = f"{self.metadata.base_url}/members/"

        raw = None
        for url in [json_url, html_url]:
            try:
                resp = await self.client.get(url, headers=headers, timeout=15,
                                             follow_redirects=True)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")

                if "application/json" in ct:
                    data    = resp.json()
                    members = data.get("members", data.get("players", []))
                else:
                    html    = resp.text
                    names   = re.findall(r'"(?:name|username|ingame)"\s*:\s*"([^"]+)"', html)
                    if not names:
                        # Fallback: pick from link text
                        names = re.findall(
                            r'<(?:a|h\d)[^>]*>\s*([A-Za-z0-9_\-]{3,20})\s*</', html
                        )
                    members = [{"name": n} for n in set(names)]

                # Filtrar por identifier
                matched = [
                    m for m in members
                    if identifier.lower() in (m.get("name") or m.get("username") or "").lower()
                ] if identifier != "__roster__" else members

                if matched:
                    player = matched[0]
                    raw = {
                        "nickname":    player.get("name") or player.get("username") or identifier,
                        "real_name":   player.get("real_name"),
                        "team":        "DetonatioN FocusMe",
                        "role":        player.get("role") or player.get("position"),
                        "country":     "JP",
                        "server":      "JP",
                        "game":        game.upper(),
                        "profile_url": player.get("url") or player.get("twitter"),
                        "stats":       {},
                    }
                    break

            except Exception as e:
                self.logger.debug(f"  DetonatioN attempt failed ({url}): {e}")
                continue

        if not raw:
            self._record_failure()
            return None

        self._record_success()
        return self._normalize_to_bronze_schema(raw)

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw["nickname"],
            "game":        raw.get("game", "LOL"),
            "country":     "JP",
            "server":      "JP",
            "team":        raw.get("team"),
            "role":        raw.get("role"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "detonation",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Game-i.daa.jp — Japan game popularity rankings
# ─────────────────────────────────────────────────────────────────────────────

class GameiJapanAdapter(BaseStrategicAdapter):
    """
    Adapter para game-i.daa.jp (Japón).

    Fuente de datos de popularidad y rankings de títulos en el mercado japonés.
    Útil para detectar qué juegos tienen tracción en JP y qué jugadores son
    los más visibles en ese contexto.

    Base URL: https://game-i.daa.jp
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="gamei_japan",
            region=RegionProfile.JAPAN,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://game-i.daa.jp",
            requires_proxy=False,
            rate_limit_per_minute=30,
            reliability_score=0.72,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un jugador/streamer en los rankings de popularidad de Game-i.
        identifier puede ser el nombre del jugador o un ID de ranking.
        """
        self.logger.info(f"🇯🇵 Game-i.daa.jp → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.JAPAN)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.JAPAN)
        headers["Accept-Language"] = "ja-JP,ja;q=0.9,en;q=0.5"

        # Game-i utiliza slugs de juego en la URL
        game_slugs = {
            "lol":      "league-of-legends",
            "valorant": "valorant",
            "pubg":     "pubg",
            "ff":       "free-fire",
            "ml":       "mobile-legends",
        }
        slug = game_slugs.get(game.lower(), game.lower())

        search_url = f"{self.metadata.base_url}/ranking/{slug}"

        try:
            resp = await self.client.get(
                search_url, headers=headers, timeout=15, follow_redirects=True
            )
            resp.raise_for_status()
            html = resp.text

            # Extraer tabla de rankings (formato HTML)
            # Patrón: nombre del jugador en celdas de tabla
            rows = re.findall(
                r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE
            )
            players_found = []
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) >= 2:
                    clean = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                    if any(identifier.lower() in c.lower() for c in clean):
                        players_found.append(clean)

            if not players_found:
                self._record_failure()
                return None

            row_data = players_found[0]
            raw = {
                "nickname":        identifier,
                "rank_position":   row_data[0] if row_data[0].isdigit() else None,
                "popularity_score": _extract_float(row_data[-1]) if row_data else None,
                "country":         "JP",
                "server":          "JP",
                "game":            game.upper(),
                "profile_url":     f"{self.metadata.base_url}/ranking/{slug}",
                "stats": {
                    "popularity_score": _extract_float(row_data[-1]) if row_data else None,
                    "rank_position":    int(row_data[0]) if row_data and row_data[0].isdigit() else None,
                },
            }
            self._record_success()
            return self._normalize_to_bronze_schema(raw)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  Game-i HTTP {e.response.status_code}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  Game-i error: {e}")
            self._record_failure()
        return None

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "game":        raw.get("game"),
            "country":     "JP",
            "server":      "JP",
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "gamei_japan",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. PentaQ — China technical analysis / LPL deep stats
# ─────────────────────────────────────────────────────────────────────────────

class PentaQAdapter(BaseStrategicAdapter):
    """
    Adapter para PentaQ.com (China).

    PentaQ es una plataforma de análisis técnico de e-sports chinos,
    especialmente LPL y KPL. Publica reportes de rendimiento de jugadores
    con métricas avanzadas: draft win%, lane dominance, objective control.

    Base URL: https://www.pentaq.com
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="pentaq",
            region=RegionProfile.CHINA,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://www.pentaq.com",
            requires_proxy=True,  # China — puede requerir proxy
            rate_limit_per_minute=15,
            reliability_score=0.80,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=3, max=12),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        self.logger.info(f"🇨🇳 PentaQ → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.CHINA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.CHINA)

        # PentaQ usa una API interna con endpoints de búsqueda
        search_url = f"{self.metadata.base_url}/api/player/search"
        params = {"keyword": identifier, "game": game}

        try:
            resp = await self.client.get(
                search_url, headers=headers, params=params,
                timeout=20, follow_redirects=True
            )
            resp.raise_for_status()

            ct = resp.headers.get("content-type", "")
            if "application/json" not in ct:
                # HTML fallback: buscar nombre en página de búsqueda
                html     = resp.text
                html_url = f"{self.metadata.base_url}/player/{identifier}"
                resp2    = await self.client.get(html_url, headers=headers, timeout=15)
                resp2.raise_for_status()
                html = resp2.text

                data = self._parse_pentaq_html(html, identifier)
            else:
                json_data  = resp.json()
                players    = json_data.get("data", {}).get("players", [])
                player_raw = next(
                    (p for p in players if identifier.lower() in (p.get("name") or "").lower()),
                    players[0] if players else {}
                )
                data = self._parse_pentaq_json(player_raw, identifier)

            if not data:
                self._record_failure()
                return None

            self._record_success()
            return self._normalize_to_bronze_schema(data)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  PentaQ HTTP {e.response.status_code}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  PentaQ error: {e}")
            self._record_failure()
        return None

    def _parse_pentaq_json(self, player: Dict[str, Any], fallback: str) -> Dict[str, Any]:
        return {
            "nickname":          player.get("name") or fallback,
            "real_name":         player.get("real_name"),
            "team":              player.get("team"),
            "role":              player.get("role"),
            "country":           "CN",
            "server":            player.get("server", "Ionia"),
            "game":              "LOL",
            "profile_url":       player.get("url"),
            "stats": {
                "win_rate":         player.get("win_rate"),
                "kda":              player.get("kda"),
                "games_analyzed":   player.get("games_played"),
                "draft_win_pct":    player.get("draft_win_pct"),
                "lane_dominance":   player.get("lane_dominance"),
                "objective_ctrl":   player.get("objective_control"),
            },
        }

    def _parse_pentaq_html(self, html: str, fallback: str) -> Optional[Dict[str, Any]]:
        """Parseo ligero de HTML de PentaQ para extraer métricas."""
        win_rate = _extract_percent(html) if "%" in html else None
        kda_m    = re.search(r'KDA[^\d]*(\d+\.?\d*)', html, re.IGNORECASE)
        kda      = float(kda_m.group(1)) if kda_m else None

        name_m   = re.search(r'<h1[^>]*>\s*([^<]{2,30})\s*</h1>', html)
        name     = name_m.group(1).strip() if name_m else fallback

        return {
            "nickname":  name,
            "country":   "CN",
            "server":    "Ionia",
            "game":      "LOL",
            "profile_url": f"{self.metadata.base_url}/player/{fallback}",
            "stats": {
                "win_rate": win_rate,
                "kda":      kda,
            },
        }

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "game":        raw.get("game", "LOL"),
            "country":     "CN",
            "server":      raw.get("server"),
            "team":        raw.get("team"),
            "role":        raw.get("role"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "pentaq",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 6. VRL Vyper — Valorant South Asia league data
# ─────────────────────────────────────────────────────────────────────────────

class VRLVyperAdapter(BaseStrategicAdapter):
    """
    Adapter para VRL Vyper (India / Valorant South Asia).

    VRL Vyper es la principal liga de Valorant en la región SOUTHASIA.
    Usa la API de Battlefy (plataforma de brackets) como backend.

    Battlefy API endpoint:
        GET https://api.battlefy.com/tournaments?game=valorant&region=southasia
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="vrl_vyper",
            region=RegionProfile.INDIA,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://api.battlefy.com",
            requires_proxy=False,
            rate_limit_per_minute=40,
            reliability_score=0.77,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "valorant",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        self.logger.info(f"🇮🇳 VRL Vyper → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.INDIA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.INDIA)
        headers["Accept"] = "application/json"

        # Paso 1: buscar el equipo/jugador en torneos recientes de VRL Vyper
        tourney_url = (
            f"{self.metadata.base_url}/tournaments"
            f"?game={game}&region=southasia&limit=5"
        )

        try:
            resp = await self.client.get(tourney_url, headers=headers, timeout=20)
            resp.raise_for_status()
            tournaments = resp.json()  # Lista de torneos

            if not tournaments:
                self._record_failure()
                return None

            # Paso 2: buscar el jugador en los equipos del torneo más reciente
            tourney_id = tournaments[0].get("_id") or tournaments[0].get("id")
            teams_url  = f"{self.metadata.base_url}/tournaments/{tourney_id}/teams"
            teams_resp = await self.client.get(teams_url, headers=headers, timeout=15)
            teams_resp.raise_for_status()
            teams      = teams_resp.json()

            # Buscar jugador en los rosters
            player_data: Optional[Dict[str, Any]] = None
            for team in teams:
                for player in team.get("players", []):
                    in_game = (
                        player.get("inGameName") or
                        player.get("username")  or
                        player.get("name") or ""
                    )
                    if identifier.lower() in in_game.lower():
                        player_data = {
                            "nickname":   in_game,
                            "team":       team.get("name"),
                            "country":    "IN",
                            "server":     "SOUTHASIA",
                            "game":       "VALORANT",
                            "tournament": tournaments[0].get("name"),
                            "stats":      {},
                        }
                        break
                if player_data:
                    break

            if not player_data:
                # No encontrado — devolver esqueleto con torneo
                player_data = {
                    "nickname":   identifier,
                    "country":    "IN",
                    "server":     "SOUTHASIA",
                    "game":       "VALORANT",
                    "tournament": tournaments[0].get("name") if tournaments else None,
                    "stats":      {},
                    "_partial":   True,
                }

            self._record_success()
            return self._normalize_to_bronze_schema(player_data)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  VRL Vyper HTTP {e.response.status_code}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  VRL Vyper error: {e}")
            self._record_failure()
        return None

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "game":        "VALORANT",
            "country":     "IN",
            "server":      "SOUTHASIA",
            "team":        raw.get("team"),
            "tournament":  raw.get("tournament"),
            "profile_url": None,
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "vrl_vyper",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 7. GosuGamers SEA — Dota2 / Mobile Legends SEA
# ─────────────────────────────────────────────────────────────────────────────

class GosuGamersSEAAdapter(BaseStrategicAdapter):
    """
    Adapter para GosuGamers sección SEA (Vietnam, Indonesia, Filipinas).

    Fuente de datos de Dota 2 y Mobile Legends en el sudeste asiático.
    GosuGamers indexa resultados de torneos y perfiles de jugadores
    para las regiones Vietnam e Indonesia principalmente.

    Base URL: https://www.gosugamers.net
    """

    _GAME_SLUGS = {
        "dota2": "dota2",
        "ml":    "mobile-legends",
        "lol":   "lol",
        "cs2":   "cs2",
    }

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="gosugamers_sea",
            region=RegionProfile.SEA,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://www.gosugamers.net",
            requires_proxy=False,
            rate_limit_per_minute=30,
            reliability_score=0.76,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "dota2",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        self.logger.info(f"🌏 GosuGamers SEA → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.SEA)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.SEA)

        game_slug = self._GAME_SLUGS.get(game.lower(), game.lower())

        # GosuGamers tiene una API de búsqueda semi-pública
        search_url = f"{self.metadata.base_url}/api/{game_slug}/players"
        params     = {"search": identifier, "region": "sea", "limit": 5}

        try:
            resp = await self.client.get(
                search_url, headers=headers, params=params,
                timeout=20, follow_redirects=True
            )
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")

            if "application/json" in ct:
                data    = resp.json()
                players = data.get("players", data.get("results", []))
                player  = next(
                    (p for p in players
                     if identifier.lower() in (p.get("name") or "").lower()),
                    players[0] if players else {}
                )
            else:
                # HTML fallback
                html   = resp.text
                names  = re.findall(
                    r'href="/' + game_slug + r'/players/([^"]+)"', html
                )
                player = {"name": names[0]} if names else {}

            if not player:
                self._record_failure()
                return None

            raw = {
                "nickname":    player.get("name") or identifier,
                "real_name":   player.get("real_name"),
                "team":        player.get("team", {}).get("name") if isinstance(player.get("team"), dict) else player.get("team"),
                "country":     player.get("country_code", "SEA"),
                "server":      "SEA",
                "game":        game.upper(),
                "profile_url": f"{self.metadata.base_url}/{game_slug}/players/{player.get('slug', identifier)}",
                "stats": {
                    "win_rate":         player.get("win_rate"),
                    "kda":              player.get("kda"),
                    "games_analyzed":   player.get("matches_played"),
                    "tournament_wins":  player.get("tournament_wins"),
                },
            }
            self._record_success()
            self.logger.success(f"✅ GosuGamers SEA {identifier}")
            return self._normalize_to_bronze_schema(raw)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  GosuGamers HTTP {e.response.status_code}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  GosuGamers error: {e}")
            self._record_failure()
        return None

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "game":        raw.get("game"),
            "country":     raw.get("country", "SEA"),
            "server":      "SEA",
            "team":        raw.get("team"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "gosugamers_sea",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 8. Liquipedia — Global tournament/transfer backup (MediaWiki API)
# ─────────────────────────────────────────────────────────────────────────────

class LiquipediaAdapter(BaseStrategicAdapter):
    """
    Adapter para Liquipedia (global backup para todas las regiones).

    Usa la MediaWiki API oficial de Liquipedia para obtener resultados de
    torneos, historial de equipos y datos de transferencias.
    No requiere reverse engineering — MediaWiki API es pública.

    Rate limit: ~1 req/2s por IP (respetamos con ExponentialBackoffHandler)

    Wikis soportadas: leagueoflegends, valorant, dota2, pubg, rocketleague
    """

    _WIKI_MAP = {
        "lol":      "leagueoflegends",
        "valorant": "valorant",
        "dota2":    "dota2",
        "pubg":     "pubg",
        "rl":       "rocketleague",
        "ml":       "mobilelegends",
    }

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        metadata = SourceMetadata(
            source_name="liquipedia",
            region=RegionProfile.GLOBAL,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://liquipedia.net",
            requires_proxy=False,
            rate_limit_per_minute=25,   # ~1 req / 2.4s — conservador
            reliability_score=0.95,
        )
        super().__init__(client, metadata)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=3, max=15),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de un jugador desde la Liquipedia MediaWiki API.
        identifier = nombre del jugador tal como aparece en Liquipedia (ej: "Faker")
        """
        self.logger.info(f"📚 Liquipedia → {identifier} ({game})")
        await ExponentialBackoffHandler.delay(RegionProfile.GLOBAL)
        headers = AdvancedHeaderRotator.get_headers(RegionProfile.GLOBAL)
        # Liquipedia requiere User-Agent descriptivo
        headers["User-Agent"] = (
            "GameRadar-AI/1.0 (https://github.com/marcelodanieldm/gameradar; "
            "data-ingestion-bot) python-httpx"
        )
        headers["Accept"] = "application/json"

        wiki = self._WIKI_MAP.get(game.lower(), "leagueoflegends")
        api_url = f"{self.metadata.base_url}/{wiki}/api.php"

        params = {
            "action":      "parse",
            "page":        identifier,
            "prop":        "wikitext|categories",
            "format":      "json",
            "redirects":   "1",
        }

        try:
            resp = await self.client.get(
                api_url, headers=headers, params=params,
                timeout=20, follow_redirects=True
            )
            resp.raise_for_status()
            data = resp.json()

            parse_data = data.get("parse", {})
            wikitext   = parse_data.get("wikitext", {}).get("*", "")
            page_title = parse_data.get("title", identifier)

            if not wikitext:
                self._record_failure()
                return None

            raw = self._parse_wikitext(wikitext, page_title, identifier, game, wiki)
            self._record_success()
            self.logger.success(f"✅ Liquipedia [{wiki}] {identifier}")
            return self._normalize_to_bronze_schema(raw)

        except httpx.HTTPStatusError as e:
            self.logger.warning(f"⚠️  Liquipedia HTTP {e.response.status_code} → {identifier}")
            self._record_failure()
        except Exception as e:
            self.logger.warning(f"⚠️  Liquipedia error → {identifier}: {e}")
            self._record_failure()
        return None

    def _parse_wikitext(
        self, wikitext: str, page_title: str,
        identifier: str, game: str, wiki: str,
    ) -> Dict[str, Any]:
        """Extrae campos clave del wikitext de un artículo de jugador."""

        def _field(key: str) -> Optional[str]:
            """Extrae valor de |key = valor en wikitext."""
            m = re.search(
                rf'\|\s*{key}\s*=\s*([^\|\n\}}]+)',
                wikitext, re.IGNORECASE
            )
            if m:
                val = re.sub(r'\[\[([^\|\]]+\|)?([^\]]+)\]\]', r'\2', m.group(1))
                return val.strip() or None
            return None

        id_field   = _field("id")    or page_title
        name_field = _field("name")  or _field("realname")
        team_field = _field("team")  or _field("team1")
        country_f  = _field("country") or _field("nationality")
        role_f     = _field("role")  or _field("position")
        birth_f    = _field("birth_date")
        twitter_f  = _field("twitter")

        # Extraer país del wikitext
        country_code = "XX"
        if country_f:
            cc = re.search(r'\b([A-Z]{2})\b', country_f)
            country_code = cc.group(1) if cc else country_f[:2].upper()

        return {
            "nickname":    id_field,
            "real_name":   name_field,
            "team":        team_field,
            "role":        role_f,
            "country":     country_code,
            "server":      country_code,
            "game":        game.upper(),
            "birth_date":  birth_f,
            "twitter":     twitter_f,
            "profile_url": f"https://liquipedia.net/{wiki}/{urllib.parse.quote(identifier)}",
            "stats":       {},   # Liquipedia no provee stats en tiempo real
            "_liquipedia_wiki": wiki,
        }

    def _normalize_to_bronze_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nickname":    raw.get("nickname"),
            "real_name":   raw.get("real_name"),
            "game":        raw.get("game"),
            "country":     raw.get("country"),
            "server":      raw.get("server"),
            "team":        raw.get("team"),
            "role":        raw.get("role"),
            "profile_url": raw.get("profile_url"),
            "stats":       raw.get("stats", {}),
            "raw_data":    raw,
            "source":      "liquipedia",
            "scraped_at":  _now(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Registry extension — registrar en StrategicAdapterFactory
# ─────────────────────────────────────────────────────────────────────────────

ASIA_ADAPTERS: Dict[str, type] = {
    "opgg_kr":         OPGGAdapter,
    "opgg_jp":         OPGGAdapter,
    "zeta_division":   ZetaDivisionAdapter,
    "detonation":      DetonatioNAdapter,
    "gamei_japan":     GameiJapanAdapter,
    "pentaq":          PentaQAdapter,
    "vrl_vyper":       VRLVyperAdapter,
    "gosugamers_sea":  GosuGamersSEAAdapter,
    "liquipedia":      LiquipediaAdapter,
}

# Constructor kwargs especiales por fuente
ASIA_ADAPTER_KWARGS: Dict[str, Dict[str, Any]] = {
    "opgg_kr": {"region": "kr"},
    "opgg_jp": {"region": "jp"},
}
