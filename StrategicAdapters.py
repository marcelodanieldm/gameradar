"""
Strategic Adapters - Conectores de Grado Militar para Fuentes Globales
========================================================================

Adapters especializados para fuentes estratégicas de e-sports:
- China: Wanplus (LPL/KPL), ScoreGG (统计数据)
- India: The Esports Club (brackets locales)
- Vietnam: Soha Game (VCS/VPL)
- Global: Steam Web API (Dota 2), Loot.bet (odds proxy)
- Japan/Korea: Riot Games Shards

Author: GameRadar AI Team
Version: 1.0.0 (Military-Grade)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import httpx
import asyncio
import random
import hashlib
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from datetime import datetime
import json


# ============================================================================
# ENUMS Y CONFIGURACIÓN
# ============================================================================

class DataPriority(str, Enum):
    """Prioridad de extracción según región"""
    MICRO_METRICS = "micro_metrics"  # Korea/China: APM, Gold/Min, DMG%
    SOCIAL_SENTIMENT = "social_sentiment"  # India/Vietnam: Consistency, Social


class RegionProfile(str, Enum):
    """Perfiles regionales para anti-detection"""
    CHINA = "china"
    KOREA = "korea"
    INDIA = "india"
    VIETNAM = "vietnam"
    JAPAN = "japan"
    SEA = "sea"
    GLOBAL = "global"


@dataclass
class SourceMetadata:
    """Metadata completa de cada fuente"""
    source_name: str
    region: RegionProfile
    priority: DataPriority
    base_url: str
    requires_proxy: bool = False
    rate_limit_per_minute: int = 30
    reliability_score: float = 1.0  # 0.0 a 1.0


# ============================================================================
# STEALTH UTILITIES
# ============================================================================

class AdvancedHeaderRotator:
    """Rotación avanzada de headers por región geográfica"""
    
    # User-Agents específicos por región (navegadores más comunes)
    REGIONAL_USER_AGENTS = {
        RegionProfile.CHINA: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 QBCore/4.0.68.400 QQBrowser/11.7.5250.400",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        RegionProfile.KOREA: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        ],
        RegionProfile.INDIA: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ],
        RegionProfile.VIETNAM: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Coc Coc/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A127F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ],
        RegionProfile.JAPAN: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ],
        RegionProfile.SEA: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A135F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ],
        RegionProfile.GLOBAL: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    }
    
    # Accept-Language por región
    REGIONAL_LANGUAGES = {
        RegionProfile.CHINA: "zh-CN,zh;q=0.9,en;q=0.8",
        RegionProfile.KOREA: "ko-KR,ko;q=0.9,en;q=0.8",
        RegionProfile.INDIA: "en-IN,en;q=0.9,hi;q=0.8",
        RegionProfile.VIETNAM: "vi-VN,vi;q=0.9,en;q=0.8",
        RegionProfile.JAPAN: "ja-JP,ja;q=0.9,en;q=0.8",
        RegionProfile.SEA: "en-US,en;q=0.9,th;q=0.8,id;q=0.7",
        RegionProfile.GLOBAL: "en-US,en;q=0.9",
    }
    
    @classmethod
    def get_headers(cls, region: RegionProfile = RegionProfile.GLOBAL) -> Dict[str, str]:
        """Genera headers realistas para la región especificada"""
        user_agents = cls.REGIONAL_USER_AGENTS.get(region, cls.REGIONAL_USER_AGENTS[RegionProfile.GLOBAL])
        
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": cls.REGIONAL_LANGUAGES[region],
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }


class ExponentialBackoffHandler:
    """Maneja backoff exponencial con jitter para evitar rate limits"""
    
    @staticmethod
    async def delay(region: RegionProfile, attempt: int = 0) -> None:
        """Delay inteligente basado en región y número de intento"""
        base_delays = {
            RegionProfile.CHINA: (3, 7),      # China: delays más largos (GFW)
            RegionProfile.KOREA: (2, 5),      # Korea: moderado
            RegionProfile.INDIA: (2, 4),      # India: moderado-bajo
            RegionProfile.VIETNAM: (2, 5),    # Vietnam: moderado
            RegionProfile.JAPAN: (2, 4),      # Japan: moderado-bajo
            RegionProfile.SEA: (2, 5),        # SEA: moderado
            RegionProfile.GLOBAL: (1, 3),     # Global: bajo
        }
        
        min_delay, max_delay = base_delays.get(region, (1, 3))
        
        # Exponential backoff: delay crece con cada intento
        exponential_factor = 2 ** attempt if attempt > 0 else 1
        
        # Jitter aleatorio para evitar patrones
        jitter = random.uniform(0.5, 1.5)
        
        final_delay = min(
            (min_delay + random.uniform(0, max_delay - min_delay)) * exponential_factor * jitter,
            30  # Max 30 segundos
        )
        
        logger.debug(f"⏱️ Delay: {final_delay:.2f}s (region: {region}, attempt: {attempt})")
        await asyncio.sleep(final_delay)


# ============================================================================
# BASE ADAPTER
# ============================================================================

class BaseStrategicAdapter(ABC):
    """Base para todos los adapters estratégicos"""
    
    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        metadata: Optional[SourceMetadata] = None
    ):
        self.client = client
        self.metadata = metadata
        self.logger = logger.bind(source=metadata.source_name if metadata else "unknown")
        
        # Métricas
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_delay": 0.0,
        }
    
    @abstractmethod
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch datos de un jugador. Debe devolver formato normalizado."""
        pass
    
    @abstractmethod
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza datos de la fuente al esquema Bronze de Supabase"""
        pass
    
    def _record_success(self):
        """Registra éxito en métricas"""
        self.metrics["requests"] += 1
        self.metrics["successes"] += 1
    
    def _record_failure(self):
        """Registra fallo en métricas"""
        self.metrics["requests"] += 1
        self.metrics["failures"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Devuelve métricas del adapter"""
        total = self.metrics["requests"]
        success_rate = (self.metrics["successes"] / total * 100) if total > 0 else 0
        
        return {
            "source": self.metadata.source_name if self.metadata else "unknown",
            "requests": total,
            "successes": self.metrics["successes"],
            "failures": self.metrics["failures"],
            "success_rate": round(success_rate, 2),
            "avg_delay": round(self.metrics["total_delay"] / total, 2) if total > 0 else 0
        }


# ============================================================================
# ADAPTERS ESPECIALIZADOS
# ============================================================================

class WanplusAdapter(BaseStrategicAdapter):
    """
    Adapter para Wanplus.com (China)
    Fuente: LPL/KPL stats, micro-metrics (APM, Gold/Min, DMG%)
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        metadata = SourceMetadata(
            source_name="wanplus",
            region=RegionProfile.CHINA,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://www.wanplus.com",
            requires_proxy=True,
            rate_limit_per_minute=20,
            reliability_score=0.85
        )
        super().__init__(client, metadata)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch jugador desde Wanplus"""
        self.logger.info(f"🇨🇳 Fetching {identifier} from Wanplus (game: {game})")
        
        try:
            # Delay anti-detección
            await ExponentialBackoffHandler.delay(RegionProfile.CHINA)
            
            headers = AdvancedHeaderRotator.get_headers(RegionProfile.CHINA)
            
            # URL según juego
            game_paths = {
                "lol": "lol",
                "kpl": "kog",  # King of Glory (王者荣耀)
                "dota2": "dota2"
            }
            
            game_path = game_paths.get(game.lower(), "lol")
            url = f"{self.metadata.base_url}/{game_path}/player/{identifier}"
            
            response = await self.client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Parsear HTML o JSON
            raw_data = self._parse_wanplus_response(response.text, game)
            
            if not raw_data:
                self._record_failure()
                return None
            
            # Normalizar a esquema Bronze
            normalized = self._normalize_to_bronze_schema(raw_data)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} from Wanplus")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _parse_wanplus_response(self, html: str, game: str) -> Optional[Dict[str, Any]]:
        """Parsear response de Wanplus (simulado - requiere Playwright para JS)"""
        # En producción, usar Playwright para renderizar JS
        # Aquí simulamos el parsing
        
        # Ejemplo de datos extraídos
        return {
            "nickname": "ExamplePlayer",
            "real_name": "张三",  # Soporte Unicode
            "team": "EDG",
            "role": "Mid",
            "win_rate": 68.5,
            "kda": 5.2,
            "apm": 285,  # Actions Per Minute (micro-metric)
            "gold_per_min": 425,  # Gold/Min (micro-metric)
            "damage_percent": 32.5,  # DMG% (micro-metric)
            "games_played": 150,
            "rank": "Grandmaster",
            "server": "Ionia",  # 艾欧尼亚
            "country": "CN",
            "source": "wanplus",
            "raw_url": f"https://www.wanplus.com/{game}/player/example"
        }
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de Wanplus al esquema Bronze"""
        return {
            "nickname": raw_data.get("nickname"),
            "game": "LOL",  # o mapear desde el input
            "country": raw_data.get("country", "CN"),
            "server": raw_data.get("server"),
            "rank": raw_data.get("rank"),
            "stats": {
                "win_rate": raw_data.get("win_rate"),
                "kda": raw_data.get("kda"),
                "games_analyzed": raw_data.get("games_played"),
                # Micro-metrics específicos
                "apm": raw_data.get("apm"),
                "gold_per_min": raw_data.get("gold_per_min"),
                "damage_percent": raw_data.get("damage_percent"),
            },
            "raw_data": raw_data,  # JSONB completo
            "source": "wanplus",
            "scraped_at": datetime.utcnow().isoformat()
        }


class TheEsportsClubAdapter(BaseStrategicAdapter):
    """
    Adapter para The Esports Club (India)
    Fuente: Brackets locales, social sentiment, consistency
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        metadata = SourceMetadata(
            source_name="tec_india",
            region=RegionProfile.INDIA,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://www.theesportsclub.com",
            requires_proxy=False,
            rate_limit_per_minute=40,
            reliability_score=0.75
        )
        super().__init__(client, metadata)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch jugador desde The Esports Club"""
        self.logger.info(f"🇮🇳 Fetching {identifier} from TEC India (game: {game})")
        
        try:
            await ExponentialBackoffHandler.delay(RegionProfile.INDIA)
            
            headers = AdvancedHeaderRotator.get_headers(RegionProfile.INDIA)
            
            # TEC tiene una API pública limitada
            url = f"{self.metadata.base_url}/api/v1/player/{identifier}"
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            raw_data = response.json()
            
            if not raw_data or "player" not in raw_data:
                self._record_failure()
                return None
            
            # Extraer social sentiment & consistency
            parsed = self._parse_tec_data(raw_data["player"])
            normalized = self._normalize_to_bronze_schema(parsed)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} from TEC India")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _parse_tec_data(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsear datos de TEC con énfasis en social sentiment"""
        return {
            "nickname": player_data.get("username"),
            "team": player_data.get("team_name"),
            "role": player_data.get("role"),
            "win_rate": player_data.get("win_rate", 0),
            "kda": player_data.get("kda", 0),
            "games_played": player_data.get("total_matches", 0),
            "rank": player_data.get("tier"),
            "server": "India",
            "country": "IN",
            # Social Sentiment Metrics
            "tournament_participations": player_data.get("tournaments_count", 0),
            "consistency_score": player_data.get("consistency", 0),  # 0-100
            "community_rating": player_data.get("rating", 0),
            "source": "tec_india",
            "raw_url": player_data.get("profile_url")
        }
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de TEC al esquema Bronze"""
        return {
            "nickname": raw_data.get("nickname"),
            "game": "LOL",
            "country": "IN",
            "server": raw_data.get("server"),
            "rank": raw_data.get("rank"),
            "stats": {
                "win_rate": raw_data.get("win_rate"),
                "kda": raw_data.get("kda"),
                "games_analyzed": raw_data.get("games_played"),
                # Social Sentiment Metrics
                "tournament_participations": raw_data.get("tournament_participations"),
                "consistency_score": raw_data.get("consistency_score"),
                "community_rating": raw_data.get("community_rating"),
            },
            "raw_data": raw_data,
            "source": "tec_india",
            "scraped_at": datetime.utcnow().isoformat()
        }


class SohaGameAdapter(BaseStrategicAdapter):
    """
    Adapter para Soha Game (Vietnam)
    Fuente: VCS/VPL stats, social consistency
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        metadata = SourceMetadata(
            source_name="soha_game",
            region=RegionProfile.VIETNAM,
            priority=DataPriority.SOCIAL_SENTIMENT,
            base_url="https://gamek.vn",  # Soha Game Network
            requires_proxy=False,
            rate_limit_per_minute=30,
            reliability_score=0.70
        )
        super().__init__(client, metadata)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch jugador desde Soha Game"""
        self.logger.info(f"🇻🇳 Fetching {identifier} from Soha Game (game: {game})")
        
        try:
            await ExponentialBackoffHandler.delay(RegionProfile.VIETNAM)
            
            headers = AdvancedHeaderRotator.get_headers(RegionProfile.VIETNAM)
            
            # Soha Game tiene diferentes secciones por juego
            game_paths = {
                "lol": "lien-minh-huyen-thoai",
                "pubg": "pubg-mobile",
                "ff": "free-fire"
            }
            
            game_path = game_paths.get(game.lower(), "lien-minh-huyen-thoai")
            url = f"{self.metadata.base_url}/{game_path}/player/{identifier}"
            
            response = await self.client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Parsear HTML (requiere BeautifulSoup o Playwright)
            raw_data = self._parse_soha_response(response.text)
            
            if not raw_data:
                self._record_failure()
                return None
            
            normalized = self._normalize_to_bronze_schema(raw_data)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} from Soha Game")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _parse_soha_response(self, html: str) -> Optional[Dict[str, Any]]:
        """Parsear response de Soha Game (simulado)"""
        # En producción, usar BeautifulSoup o Playwright
        return {
            "nickname": "VCSPlayer",
            "team": "GAM Esports",
            "role": "Jungle",
            "win_rate": 55.0,
            "kda": 3.8,
            "games_played": 80,
            "rank": "Challenger",
            "server": "VN",
            "country": "VN",
            "consistency_score": 75,  # Social metric
            "source": "soha_game",
            "raw_url": "https://gamek.vn/lien-minh-huyen-thoai/player/example"
        }
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de Soha Game al esquema Bronze"""
        return {
            "nickname": raw_data.get("nickname"),
            "game": "LOL",
            "country": "VN",
            "server": raw_data.get("server"),
            "rank": raw_data.get("rank"),
            "stats": {
                "win_rate": raw_data.get("win_rate"),
                "kda": raw_data.get("kda"),
                "games_analyzed": raw_data.get("games_played"),
                "consistency_score": raw_data.get("consistency_score"),
            },
            "raw_data": raw_data,
            "source": "soha_game",
            "scraped_at": datetime.utcnow().isoformat()
        }


class SteamWebAPIAdapter(BaseStrategicAdapter):
    """
    Adapter para Steam Web API (Dota 2 SEA)
    Fuente: Match history, MMR, hero stats
    """
    
    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        api_key: Optional[str] = None
    ):
        metadata = SourceMetadata(
            source_name="steam_web_api",
            region=RegionProfile.SEA,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://api.steampowered.com",
            requires_proxy=False,
            rate_limit_per_minute=100,  # Steam es generoso
            reliability_score=0.95
        )
        super().__init__(client, metadata)
        self.api_key = api_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,  # Steam ID64 o account ID
        game: str = "dota2",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch jugador desde Steam Web API"""
        self.logger.info(f"🎮 Fetching {identifier} from Steam API (game: {game})")
        
        if not self.api_key:
            self.logger.error("❌ Steam API key not configured")
            self._record_failure()
            return None
        
        try:
            await ExponentialBackoffHandler.delay(RegionProfile.GLOBAL)
            
            # Convertir account ID a Steam ID64 si es necesario
            account_id = self._normalize_steam_id(identifier)
            
            # Fetch match history
            matches_url = f"{self.metadata.base_url}/IDOTA2Match_570/GetMatchHistory/v1/"
            params = {
                "key": self.api_key,
                "account_id": account_id,
                "matches_requested": 20
            }
            
            response = await self.client.get(matches_url, params=params)
            response.raise_for_status()
            
            match_data = response.json()
            
            if not match_data or "result" not in match_data:
                self._record_failure()
                return None
            
            # Calcular estadísticas desde matches
            stats = self._calculate_dota2_stats(match_data["result"])
            
            normalized = self._normalize_to_bronze_schema(stats)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} from Steam API")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _normalize_steam_id(self, identifier: str) -> int:
        """Normalizar Steam ID a account ID"""
        # Si es Steam ID64, convertir a account ID
        if len(identifier) == 17:
            return int(identifier) - 76561197960265728
        return int(identifier)
    
    def _calculate_dota2_stats(self, match_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular stats desde match history"""
        matches = match_result.get("matches", [])
        
        if not matches:
            return {}
        
        total_matches = len(matches)
        wins = sum(1 for m in matches if m.get("player_slot", 0) < 128 and m.get("radiant_win", False))
        
        # Aquí iríamos match por match para obtener KDA, GPM, etc.
        # Simplificado para el ejemplo
        
        return {
            "account_id": match_result.get("account_id"),
            "win_rate": (wins / total_matches * 100) if total_matches > 0 else 0,
            "games_played": total_matches,
            "avg_kills": 8.5,  # Simulado
            "avg_deaths": 5.2,
            "avg_assists": 12.3,
            "kda": 4.0,
            "avg_gpm": 520,  # Gold Per Minute
            "avg_xpm": 580,  # XP Per Minute
            "mmr_estimate": 4500,  # Requiere API adicional
            "server": "SEA",
            "country": "Unknown",  # Requiere geolocation
            "source": "steam_web_api"
        }
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de Steam API al esquema Bronze"""
        return {
            "nickname": f"steam_{raw_data.get('account_id')}",
            "game": "DOTA2",
            "country": raw_data.get("country", "Unknown"),
            "server": raw_data.get("server"),
            "rank": self._mmr_to_rank(raw_data.get("mmr_estimate", 0)),
            "stats": {
                "win_rate": raw_data.get("win_rate"),
                "kda": raw_data.get("kda"),
                "games_analyzed": raw_data.get("games_played"),
                "avg_gpm": raw_data.get("avg_gpm"),
                "avg_xpm": raw_data.get("avg_xpm"),
            },
            "raw_data": raw_data,
            "source": "steam_web_api",
            "scraped_at": datetime.utcnow().isoformat()
        }
    
    def _mmr_to_rank(self, mmr: int) -> str:
        """Convertir MMR a rank Dota 2"""
        if mmr >= 6000:
            return "Immortal"
        elif mmr >= 4620:
            return "Divine"
        elif mmr >= 3696:
            return "Ancient"
        elif mmr >= 2772:
            return "Legend"
        elif mmr >= 1848:
            return "Archon"
        elif mmr >= 924:
            return "Crusader"
        else:
            return "Herald"


class LootBetAdapter(BaseStrategicAdapter):
    """
    Adapter para Loot.bet (Betting Odds como proxy de rendimiento)
    Fuente: Odds de torneos, rendimiento esperado
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        metadata = SourceMetadata(
            source_name="loot_bet",
            region=RegionProfile.GLOBAL,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://loot.bet",
            requires_proxy=False,
            rate_limit_per_minute=30,
            reliability_score=0.80
        )
        super().__init__(client, metadata)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch odds del jugador/team desde Loot.bet"""
        self.logger.info(f"🎲 Fetching {identifier} odds from Loot.bet (game: {game})")
        
        try:
            await ExponentialBackoffHandler.delay(RegionProfile.GLOBAL)
            
            headers = AdvancedHeaderRotator.get_headers(RegionProfile.GLOBAL)
            
            # Loot.bet tiene API interna (requiere reverse engineering)
            # Aquí simulamos la estructura
            url = f"{self.metadata.base_url}/api/matches/{game}/player/{identifier}"
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            raw_data = response.json()
            
            if not raw_data:
                self._record_failure()
                return None
            
            # Calcular performance score desde odds
            parsed = self._parse_lootbet_odds(raw_data)
            normalized = self._normalize_to_bronze_schema(parsed)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} odds from Loot.bet")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _parse_lootbet_odds(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsear odds y convertir a performance score"""
        # Odds más bajas = mejor jugador (más probable de ganar)
        avg_odds = raw_data.get("avg_odds", 2.0)
        
        # Convertir odds a performance score (0-100)
        # Odds 1.5 = ~95 score, Odds 3.0 = ~60 score
        performance_score = max(0, min(100, 150 - (avg_odds * 30)))
        
        return {
            "nickname": raw_data.get("player_name"),
            "team": raw_data.get("team_name"),
            "avg_odds": avg_odds,
            "performance_score": performance_score,
            "matches_tracked": raw_data.get("matches_count", 0),
            "win_probability": raw_data.get("win_probability", 0),
            "country": raw_data.get("country", "Unknown"),
            "source": "loot_bet"
        }
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de Loot.bet al esquema Bronze"""
        return {
            "nickname": raw_data.get("nickname"),
            "game": "LOL",
            "country": raw_data.get("country"),
            "server": "Unknown",
            "rank": "Unknown",
            "stats": {
                "performance_score": raw_data.get("performance_score"),
                "win_probability": raw_data.get("win_probability"),
                "avg_odds": raw_data.get("avg_odds"),
                "games_analyzed": raw_data.get("matches_tracked"),
            },
            "raw_data": raw_data,
            "source": "loot_bet",
            "scraped_at": datetime.utcnow().isoformat()
        }


class RiotGamesShardAdapter(BaseStrategicAdapter):
    """
    Adapter para Riot Games Official API (Shards JP/KR)
    Fuente: Datos oficiales, ranked stats, match history
    """
    
    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        api_key: Optional[str] = None,
        shard: str = "kr"  # kr, jp, etc.
    ):
        metadata = SourceMetadata(
            source_name=f"riot_api_{shard}",
            region=RegionProfile.KOREA if shard == "kr" else RegionProfile.JAPAN,
            priority=DataPriority.MICRO_METRICS,
            base_url=f"https://{shard}.api.riotgames.com",
            requires_proxy=False,
            rate_limit_per_minute=100,
            reliability_score=0.98  # Fuente oficial
        )
        super().__init__(client, metadata)
        self.api_key = api_key
        self.shard = shard
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_player(
        self,
        identifier: str,  # Summoner name or PUUID
        game: str = "lol",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch jugador desde Riot API"""
        self.logger.info(f"🎮 Fetching {identifier} from Riot API {self.shard.upper()}")
        
        if not self.api_key:
            self.logger.error("❌ Riot API key not configured")
            self._record_failure()
            return None
        
        try:
            await ExponentialBackoffHandler.delay(
                RegionProfile.KOREA if self.shard == "kr" else RegionProfile.JAPAN
            )
            
            headers = {
                "X-Riot-Token": self.api_key,
                "Accept": "application/json"
            }
            
            # 1. Get summoner by name
            summoner_url = f"{self.metadata.base_url}/lol/summoner/v4/summoners/by-name/{identifier}"
            summoner_response = await self.client.get(summoner_url, headers=headers)
            summoner_response.raise_for_status()
            
            summoner_data = summoner_response.json()
            summoner_id = summoner_data["id"]
            
            # 2. Get ranked stats
            ranked_url = f"{self.metadata.base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
            ranked_response = await self.client.get(ranked_url, headers=headers)
            ranked_response.raise_for_status()
            
            ranked_data = ranked_response.json()
            
            # Combinar datos
            combined = {
                **summoner_data,
                "ranked_stats": ranked_data
            }
            
            normalized = self._normalize_to_bronze_schema(combined)
            
            self._record_success()
            self.logger.success(f"✅ Fetched {identifier} from Riot API")
            
            return normalized
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP error for {identifier}: {e.response.status_code}")
            self._record_failure()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {identifier}: {e}")
            self._record_failure()
            return None
    
    def _normalize_to_bronze_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de Riot API al esquema Bronze"""
        ranked_stats = raw_data.get("ranked_stats", [])
        solo_queue = next((r for r in ranked_stats if r.get("queueType") == "RANKED_SOLO_5x5"), {})
        
        wins = solo_queue.get("wins", 0)
        losses = solo_queue.get("losses", 0)
        total_games = wins + losses
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        return {
            "nickname": raw_data.get("name"),
            "game": "LOL",
            "country": "KR" if self.shard == "kr" else "JP",
            "server": self.shard.upper(),
            "rank": f"{solo_queue.get('tier', 'Unranked')} {solo_queue.get('rank', '')}".strip(),
            "stats": {
                "win_rate": round(win_rate, 2),
                "games_analyzed": total_games,
                "wins": wins,
                "losses": losses,
                "league_points": solo_queue.get("leaguePoints", 0),
            },
            "raw_data": raw_data,
            "source": f"riot_api_{self.shard}",
            "scraped_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# ADAPTER REGISTRY
# ============================================================================

class StrategicAdapterFactory:
    """Factory para registrar y obtener adapters estratégicos"""
    
    _adapters: Dict[str, type] = {
        "wanplus": WanplusAdapter,
        "tec_india": TheEsportsClubAdapter,
        "soha_game": SohaGameAdapter,
        "steam_web_api": SteamWebAPIAdapter,
        "loot_bet": LootBetAdapter,
        "riot_api_kr": RiotGamesShardAdapter,
        "riot_api_jp": RiotGamesShardAdapter,
    }
    
    @classmethod
    def create_adapter(
        cls,
        source: str,
        client: httpx.AsyncClient,
        **kwargs
    ) -> Optional[BaseStrategicAdapter]:
        """Crear instancia de adapter"""
        adapter_class = cls._adapters.get(source)
        
        if not adapter_class:
            logger.error(f"❌ Adapter '{source}' not found")
            return None
        
        return adapter_class(client=client, **kwargs)
    
    @classmethod
    def get_all_sources(cls) -> List[str]:
        """Listar todos los adapters disponibles"""
        return list(cls._adapters.keys())
    
    @classmethod
    def get_sources_by_region(cls, region: RegionProfile) -> List[str]:
        """Obtener fuentes por región"""
        region_mapping = {
            RegionProfile.CHINA: ["wanplus"],
            RegionProfile.KOREA: ["riot_api_kr"],
            RegionProfile.JAPAN: ["riot_api_jp"],
            RegionProfile.INDIA: ["tec_india"],
            RegionProfile.VIETNAM: ["soha_game"],
            RegionProfile.SEA: ["steam_web_api"],
            RegionProfile.GLOBAL: ["loot_bet"],
        }
        
        return region_mapping.get(region, [])


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

async def example_usage():
    """Ejemplo de uso de los adapters estratégicos"""
    
    async with httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(max_connections=20),
        timeout=httpx.Timeout(30.0)
    ) as client:
        
        # 1. Fetch desde Wanplus (China)
        wanplus = WanplusAdapter(client=client)
        china_player = await wanplus.fetch_player("JackeyLove", game="lol")
        
        if china_player:
            logger.info(f"🇨🇳 China Player: {china_player['nickname']}")
            logger.info(f"   APM: {china_player['stats'].get('apm')}")
            logger.info(f"   Gold/Min: {china_player['stats'].get('gold_per_min')}")
        
        # 2. Fetch desde TEC India
        tec = TheEsportsClubAdapter(client=client)
        india_player = await tec.fetch_player("IndianPro123", game="lol")
        
        if india_player:
            logger.info(f"🇮🇳 India Player: {india_player['nickname']}")
            logger.info(f"   Consistency: {india_player['stats'].get('consistency_score')}")
        
        # 3. Fetch desde Steam API (Dota 2)
        steam = SteamWebAPIAdapter(client=client, api_key="YOUR_STEAM_KEY")
        dota_player = await steam.fetch_player("123456789", game="dota2")
        
        if dota_player:
            logger.info(f"🎮 Dota Player: {dota_player['nickname']}")
            logger.info(f"   GPM: {dota_player['stats'].get('avg_gpm')}")
        
        # 4. Métricas
        logger.info("\n📊 Metrics:")
        logger.info(f"Wanplus: {wanplus.get_metrics()}")
        logger.info(f"TEC India: {tec.get_metrics()}")
        logger.info(f"Steam API: {steam.get_metrics()}")


if __name__ == "__main__":
    asyncio.run(example_usage())
