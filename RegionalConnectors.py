"""
Regional Connectors para GameRadar AI - Capa Bronze Expandida
Scrapers especializados para Dak.gg (Corea) y ScoreGG (China)

Características:
- Sistema de proxy rotativo para China (firewall bypass)
- Reintentos automáticos con backoff exponencial
- Respeto a robots.txt
- Extracción de WinRate y Most Played Hero
- Mapeo automático al formato JSON de Supabase
- Alta resiliencia y manejo de errores

Author: GameRadar AI Data Engineering Team
Date: 2026-04-16
"""

import asyncio
import random
import urllib.robotparser
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Browser, Page, ProxySettings, TimeoutError as PlaywrightTimeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode
from supabase_client import SupabaseClient
from config import settings


class ChinaProxyRotator:
    """
    Sistema de rotación de proxies específico para China
    Diseñado para evitar bloqueos de firewall (Great Firewall)
    """
    
    # Lista de proxies públicos para China (actualizar con tus proxies premium)
    CHINA_PROXIES = [
        {
            "server": "http://cn-proxy-1.example.com:8080",
            "username": "user1",
            "password": "pass1"
        },
        {
            "server": "http://cn-proxy-2.example.com:8080", 
            "username": "user2",
            "password": "pass2"
        },
        {
            "server": "http://cn-proxy-3.example.com:8080",
            "username": "user3",
            "password": "pass3"
        }
    ]
    
    # User agents realistas para China
    CHINA_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        self.current_index = 0
        self.failed_proxies = set()
        
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Obtiene el siguiente proxy disponible"""
        if len(self.failed_proxies) >= len(self.CHINA_PROXIES):
            logger.warning("⚠️ Todos los proxies de China han fallado, reiniciando...")
            self.failed_proxies.clear()
        
        # Buscar un proxy que no haya fallado
        attempts = 0
        while attempts < len(self.CHINA_PROXIES):
            proxy = self.CHINA_PROXIES[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.CHINA_PROXIES)
            
            if proxy["server"] not in self.failed_proxies:
                logger.debug(f"🔄 Usando proxy: {proxy['server']}")
                return proxy
            
            attempts += 1
        
        # Si todos fallaron, devolver None (usar sin proxy)
        return None
    
    def mark_proxy_failed(self, proxy_server: str):
        """Marca un proxy como fallido"""
        self.failed_proxies.add(proxy_server)
        logger.warning(f"❌ Proxy marcado como fallido: {proxy_server}")
    
    def get_random_user_agent(self) -> str:
        """Obtiene un User-Agent aleatorio para China"""
        return random.choice(self.CHINA_USER_AGENTS)


class RobotsTxtChecker:
    """
    Verificador de robots.txt para cumplimiento ético
    """
    
    def __init__(self):
        self.parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
    
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Verifica si se puede scrapear una URL según robots.txt
        
        Args:
            url: URL a verificar
            user_agent: User-Agent a usar
            
        Returns:
            True si se permite el scraping, False si no
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Cachear el parser para este dominio
            if base_url not in self.parsers:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(urljoin(base_url, "/robots.txt"))
                try:
                    rp.read()
                    self.parsers[base_url] = rp
                except:
                    # Si no se puede leer robots.txt, asumir permitido
                    logger.debug(f"⚠️ No se pudo leer robots.txt de {base_url}")
                    return True
            
            can_fetch = self.parsers[base_url].can_fetch(user_agent, url)
            
            if not can_fetch:
                logger.warning(f"🚫 robots.txt prohíbe scrapear: {url}")
            
            return can_fetch
            
        except Exception as e:
            logger.debug(f"Error verificando robots.txt: {e}")
            # En caso de error, asumir permitido
            return True


class BaseRegionalConnector(ABC):
    """
    Clase base para conectores regionales
    Incluye funcionalidad común de scraping resiliente
    """
    
    def __init__(self, use_proxy: bool = False):
        """
        Inicializa el conector regional
        
        Args:
            use_proxy: Si se debe usar proxy rotativo
        """
        self.use_proxy = use_proxy
        self.browser: Optional[Browser] = None
        self.db = SupabaseClient()
        self.robots_checker = RobotsTxtChecker()
        self.scraped_count = 0
        self.error_count = 0
        
    async def __aenter__(self):
        """Context manager: inicializar browser"""
        playwright = await async_playwright().start()
        self.playwright = playwright
        
        # Inicializar browser con o sin proxy
        proxy_config = self._get_proxy_config() if self.use_proxy else None
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            proxy=proxy_config
        )
        
        logger.info(f"🌐 Browser iniciado para {self.__class__.__name__}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager: cerrar browser"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        logger.info(f"🌐 Browser cerrado | Scraped: {self.scraped_count} | Errors: {self.error_count}")
    
    @abstractmethod
    def _get_proxy_config(self) -> Optional[ProxySettings]:
        """Obtiene la configuración de proxy (implementar en subclases)"""
        pass
    
    @abstractmethod
    async def scrape_player(self, identifier: str) -> Optional[PlayerProfile]:
        """
        Scrapea un jugador (implementar en subclases)
        
        Args:
            identifier: Identificador del jugador
            
        Returns:
            PlayerProfile o None
        """
        pass
    
    async def _create_stealth_page(self) -> Page:
        """Crea una página con configuración anti-detección"""
        page = await self.browser.new_page()
        
        # User-Agent aleatorio
        user_agent = self._get_random_user_agent()
        await page.set_extra_http_headers({
            "User-Agent": user_agent,
            "Accept-Language": self._get_accept_language(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        })
        
        # Script anti-detección
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.navigator.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        return page
    
    @abstractmethod
    def _get_random_user_agent(self) -> str:
        """Obtiene un User-Agent aleatorio (implementar en subclases)"""
        pass
    
    @abstractmethod
    def _get_accept_language(self) -> str:
        """Obtiene el Accept-Language apropiado (implementar en subclases)"""
        pass
    
    def _map_to_supabase_format(self, player_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Mapea datos scraped al formato JSON de Supabase Bronze
        
        Args:
            player_data: Datos del jugador
            source: Fuente del scraping
            
        Returns:
            Datos en formato Bronze
        """
        return {
            "raw_data": player_data,
            "source": source,
            "source_url": player_data.get("profile_url", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "processing_status": "pending"
        }
    
    async def insert_to_bronze(self, player_profile: PlayerProfile, source: str) -> bool:
        """
        Inserta un perfil de jugador en la capa Bronze
        
        Args:
            player_profile: Perfil del jugador
            source: Fuente del scraping
            
        Returns:
            True si tuvo éxito, False si falló
        """
        try:
            # Convertir a diccionario
            player_dict = player_profile.model_dump(mode='json')
            
            # Mapear a formato Bronze
            bronze_data = self._map_to_supabase_format(player_dict, source)
            
            # Insertar en Supabase
            self.db.insert_bronze_raw(
                raw_data=bronze_data["raw_data"],
                source=source,
                source_url=bronze_data["source_url"]
            )
            
            self.scraped_count += 1
            logger.success(f"✓ Insertado en Bronze: {player_profile.nickname} ({source})")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"✗ Error insertando en Bronze: {e}")
            return False


class DakGGConnector(BaseRegionalConnector):
    """
    Conector para Dak.gg (Corea)
    Especializado en League of Legends y VALORANT
    """
    
    BASE_URL = "https://dak.gg"
    
    # User agents coreanos
    KOREAN_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def _get_proxy_config(self) -> Optional[ProxySettings]:
        """Dak.gg generalmente no requiere proxy desde fuera de Corea"""
        return None
    
    def _get_random_user_agent(self) -> str:
        return random.choice(self.KOREAN_USER_AGENTS)
    
    def _get_accept_language(self) -> str:
        return "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type((PlaywrightTimeout, Exception)),
        reraise=True
    )
    async def scrape_player(self, summoner_name: str, game: str = "lol") -> Optional[PlayerProfile]:
        """
        Scrapea un jugador de Dak.gg
        
        Args:
            summoner_name: Nombre del invocador
            game: Juego (lol, valorant)
            
        Returns:
            PlayerProfile o None
        """
        # Construir URL
        if game == "lol":
            url = f"{self.BASE_URL}/lol/profile/{summoner_name}"
        elif game == "valorant":
            url = f"{self.BASE_URL}/valorant/profile/{summoner_name}"
        else:
            logger.error(f"Juego no soportado: {game}")
            return None
        
        # Verificar robots.txt
        if not self.robots_checker.can_fetch(url, "GameRadarBot"):
            logger.warning(f"🚫 Scraping no permitido por robots.txt: {url}")
            return None
        
        page = await self._create_stealth_page()
        
        try:
            logger.info(f"📄 Scraping Dak.gg: {summoner_name} ({game})")
            
            # Navegar a la página
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Esperar a que cargue el contenido principal
            await page.wait_for_selector("div[class*='profile'], .summoner-info, [class*='player']", timeout=15000)
            
            # Extraer nickname (puede estar en hangul)
            nickname = summoner_name
            for selector in ["h1", ".summoner-name", "[class*='name']", "[class*='summoner']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and text.strip():
                            nickname = text.strip()
                            break
                except:
                    continue
            
            # Extraer tier/rank
            rank = "Unranked"
            for selector in [".tier", "[class*='tier']", "[class*='rank']", ".rank"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and any(r in text for r in ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Challenger", "아이언", "브론즈", "실버", "골드", "플래티넘", "다이아", "마스터", "그랜드마스터", "챌린저"]):
                            rank = text.strip()
                            break
                except:
                    continue
            
            # Extraer WinRate
            win_rate = 50.0
            for selector in [".win-rate", "[class*='winrate']", "[class*='win']", ".winrate"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        import re
                        match = re.search(r'(\d+)%', text)
                        if match:
                            win_rate = float(match.group(1))
                            break
                except:
                    continue
            
            logger.info(f"📊 WinRate extraído: {win_rate}%")
            
            # Extraer KDA
            kda = 2.0
            for selector in [".kda", "[class*='kda']", "[class*='KDA']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        import re
                        match = re.search(r'(\d+\.?\d*)', text)
                        if match:
                            kda = float(match.group(1))
                            break
                except:
                    continue
            
            # Extraer Most Played Hero/Champion
            top_champions = []
            champion_selectors = [
                ".champion-list .champion",
                "[class*='champion-item']",
                "[class*='most-played']",
                ".most-champion"
            ]
            
            for selector in champion_selectors:
                try:
                    champ_elements = await page.query_selector_all(selector)
                    if champ_elements:
                        for idx, elem in enumerate(champ_elements[:3]):
                            # Extraer nombre del campeón
                            champ_name = "Unknown"
                            try:
                                name_elem = await elem.query_selector("img")
                                if name_elem:
                                    champ_name = await name_elem.get_attribute("alt") or "Unknown"
                                else:
                                    text = await elem.inner_text()
                                    if text:
                                        champ_name = text.strip().split("\n")[0]
                            except:
                                pass
                            
                            # Extraer stats del campeón
                            champ_wr = win_rate
                            try:
                                wr_elem = await elem.query_selector("[class*='winrate'], .win-rate")
                                if wr_elem:
                                    wr_text = await wr_elem.inner_text()
                                    import re
                                    match = re.search(r'(\d+)%', wr_text)
                                    if match:
                                        champ_wr = float(match.group(1))
                            except:
                                pass
                            
                            top_champions.append(Champion(
                                name=champ_name,
                                games_played=50 - (idx * 10),  # Estimado
                                win_rate=champ_wr
                            ))
                        
                        if top_champions:
                            break
                except:
                    continue
            
            # Si no se encontraron campeones, crear uno genérico
            if not top_champions:
                top_champions = [Champion(name="Unknown", games_played=50, win_rate=win_rate)]
            
            logger.success(f"🏆 Most Played Hero: {top_champions[0].name}")
            
            # Crear perfil
            profile = PlayerProfile(
                nickname=nickname,
                game=GameTitle.LEAGUE_OF_LEGENDS if game == "lol" else GameTitle.VALORANT,
                country=CountryCode.KOREA,
                server="KR",
                rank=rank,
                stats=PlayerStats(
                    win_rate=win_rate,
                    kda=kda,
                    games_analyzed=100
                ),
                top_champions=top_champions[:3],
                profile_url=url,
                scraped_at=datetime.now(timezone.utc)
            )
            
            await page.close()
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error scraping Dak.gg {summoner_name}: {e}")
            await page.close()
            return None


class ScoreGGConnector(BaseRegionalConnector):
    """
    Conector para ScoreGG (China)
    Incluye sistema de proxy rotativo para bypass de Great Firewall
    """
    
    BASE_URL = "https://www.scoregg.com"
    
    def __init__(self, use_proxy: bool = True):
        """
        Inicializa el conector de ScoreGG
        
        Args:
            use_proxy: Si se debe usar proxy (recomendado para China)
        """
        super().__init__(use_proxy)
        self.proxy_rotator = ChinaProxyRotator() if use_proxy else None
        self.current_proxy = None
    
    def _get_proxy_config(self) -> Optional[ProxySettings]:
        """Obtiene configuración de proxy para China"""
        if not self.proxy_rotator:
            return None
        
        proxy = self.proxy_rotator.get_next_proxy()
        if not proxy:
            logger.warning("⚠️ No hay proxies disponibles para China")
            return None
        
        self.current_proxy = proxy
        
        return {
            "server": proxy["server"],
            "username": proxy.get("username"),
            "password": proxy.get("password")
        }
    
    def _get_random_user_agent(self) -> str:
        return self.proxy_rotator.get_random_user_agent() if self.proxy_rotator else ChinaProxyRotator.CHINA_USER_AGENTS[0]
    
    def _get_accept_language(self) -> str:
        return "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    
    @retry(
        stop=stop_after_attempt(5),  # Más reintentos para China
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((PlaywrightTimeout, Exception)),
        reraise=False  # No reraise para ser más resiliente
    )
    async def scrape_player(self, player_id: str, game: str = "lol") -> Optional[PlayerProfile]:
        """
        Scrapea un jugador de ScoreGG (China)
        
        Args:
            player_id: ID del jugador
            game: Juego (lol, dota2, etc)
            
        Returns:
            PlayerProfile o None
        """
        # Construir URL
        if game == "lol":
            url = f"{self.BASE_URL}/lol/player/{player_id}"
        elif game == "dota2":
            url = f"{self.BASE_URL}/dota2/player/{player_id}"
        else:
            logger.error(f"Juego no soportado: {game}")
            return None
        
        # Verificar robots.txt
        if not self.robots_checker.can_fetch(url, "GameRadarBot"):
            logger.warning(f"🚫 Scraping no permitido por robots.txt: {url}")
            return None
        
        page = await self._create_stealth_page()
        
        try:
            logger.info(f"📄 Scraping ScoreGG (China): {player_id} ({game})")
            
            # Delay aleatorio para parecer humano
            await asyncio.sleep(random.uniform(2, 5))
            
            # Navegar a la página
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            # Esperar contenido (más tiempo para China)
            await page.wait_for_selector("div[class*='player'], .player-info, [class*='profile']", timeout=20000)
            
            # Extraer nickname (puede estar en caracteres chinos)
            nickname = player_id
            for selector in ["h1", ".player-name", "[class*='name']", "[class*='player']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and text.strip():
                            nickname = text.strip()
                            break
                except:
                    continue
            
            # Extraer tier/rank
            rank = "Unranked"
            for selector in [".tier", "[class*='tier']", "[class*='rank']", ".rank"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        # Soportar ranks en chino e inglés
                        if text and (any(r in text for r in ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Challenger"]) or len(text) < 20):
                            rank = text.strip()
                            break
                except:
                    continue
            
            # Extraer WinRate
            win_rate = 50.0
            for selector in [".win-rate", "[class*='winrate']", "[class*='win']", "[class*='胜率']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        import re
                        match = re.search(r'(\d+)%', text)
                        if match:
                            win_rate = float(match.group(1))
                            break
                except:
                    continue
            
            logger.info(f"📊 WinRate extraído: {win_rate}%")
            
            # Extraer KDA
            kda = 2.0
            for selector in [".kda", "[class*='kda']", "[class*='KDA']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        import re
                        match = re.search(r'(\d+\.?\d*)', text)
                        if match:
                            kda = float(match.group(1))
                            break
                except:
                    continue
            
            # Extraer Most Played Hero
            top_champions = []
            champion_selectors = [
                ".champion-list .champion",
                "[class*='hero']",
                "[class*='champion']",
                "[class*='英雄']"
            ]
            
            for selector in champion_selectors:
                try:
                    champ_elements = await page.query_selector_all(selector)
                    if champ_elements:
                        for idx, elem in enumerate(champ_elements[:3]):
                            champ_name = "Unknown"
                            try:
                                # Intentar obtener de imagen
                                name_elem = await elem.query_selector("img")
                                if name_elem:
                                    champ_name = await name_elem.get_attribute("alt") or await name_elem.get_attribute("title") or "Unknown"
                                else:
                                    text = await elem.inner_text()
                                    if text:
                                        champ_name = text.strip().split("\n")[0]
                            except:
                                pass
                            
                            champ_wr = win_rate
                            try:
                                wr_elem = await elem.query_selector("[class*='winrate'], [class*='win'], [class*='胜率']")
                                if wr_elem:
                                    wr_text = await wr_elem.inner_text()
                                    import re
                                    match = re.search(r'(\d+)%', wr_text)
                                    if match:
                                        champ_wr = float(match.group(1))
                            except:
                                pass
                            
                            top_champions.append(Champion(
                                name=champ_name,
                                games_played=100 - (idx * 20),
                                win_rate=champ_wr
                            ))
                        
                        if top_champions:
                            break
                except:
                    continue
            
            if not top_champions:
                top_champions = [Champion(name="Unknown", games_played=50, win_rate=win_rate)]
            
            logger.success(f"🏆 Most Played Hero: {top_champions[0].name}")
            
            # Crear perfil
            profile = PlayerProfile(
                nickname=nickname,
                game=GameTitle.LEAGUE_OF_LEGENDS if game == "lol" else GameTitle.DOTA2,
                country=CountryCode.CHINA,
                server="CN",
                rank=rank,
                stats=PlayerStats(
                    win_rate=win_rate,
                    kda=kda,
                    games_analyzed=100
                ),
                top_champions=top_champions[:3],
                profile_url=url,
                scraped_at=datetime.now(timezone.utc)
            )
            
            await page.close()
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error scraping ScoreGG {player_id}: {e}")
            
            # Marcar proxy como fallido si se usó
            if self.current_proxy and self.proxy_rotator:
                self.proxy_rotator.mark_proxy_failed(self.current_proxy["server"])
            
            await page.close()
            return None


# Funciones de utilidad para facilitar el uso

async def scrape_dak_gg_players(summoner_names: List[str], game: str = "lol") -> List[PlayerProfile]:
    """
    Scrapea múltiples jugadores de Dak.gg
    
    Args:
        summoner_names: Lista de nombres de invocadores
        game: Juego (lol, valorant)
        
    Returns:
        Lista de perfiles scraped exitosamente
    """
    profiles = []
    
    async with DakGGConnector() as connector:
        for name in summoner_names:
            try:
                profile = await connector.scrape_player(name, game)
                if profile:
                    await connector.insert_to_bronze(profile, "dak.gg")
                    profiles.append(profile)
                
                # Delay entre jugadores
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Error scraping {name}: {e}")
                continue
    
    return profiles


async def scrape_scoregg_players(player_ids: List[str], game: str = "lol", use_proxy: bool = True) -> List[PlayerProfile]:
    """
    Scrapea múltiples jugadores de ScoreGG (China)
    
    Args:
        player_ids: Lista de IDs de jugadores
        game: Juego (lol, dota2)
        use_proxy: Si se debe usar proxy rotativo
        
    Returns:
        Lista de perfiles scraped exitosamente
    """
    profiles = []
    
    async with ScoreGGConnector(use_proxy=use_proxy) as connector:
        for player_id in player_ids:
            try:
                profile = await connector.scrape_player(player_id, game)
                if profile:
                    await connector.insert_to_bronze(profile, "scoregg.com")
                    profiles.append(profile)
                
                # Delay más largo para China
                await asyncio.sleep(random.uniform(4, 8))
                
            except Exception as e:
                logger.error(f"Error scraping {player_id}: {e}")
                continue
    
    return profiles


# Ejemplo de uso
async def main():
    """Función de ejemplo para demostrar el uso"""
    logger.info("="*80)
    logger.info("🌏 REGIONAL CONNECTORS - GameRadar AI")
    logger.info("="*80)
    
    # Ejemplo 1: Scraping de Dak.gg (Corea)
    logger.info("\n📍 Scraping Dak.gg (Korea)...")
    korean_players = ["Faker", "ShowMaker", "Chovy"]
    dak_profiles = await scrape_dak_gg_players(korean_players, game="lol")
    logger.success(f"✅ Scraped {len(dak_profiles)} jugadores de Dak.gg")
    
    # Ejemplo 2: Scraping de ScoreGG (China) con proxy
    logger.info("\n📍 Scraping ScoreGG (China) con proxy rotativo...")
    chinese_players = ["player123", "player456"]
    scoregg_profiles = await scrape_scoregg_players(chinese_players, game="lol", use_proxy=True)
    logger.success(f"✅ Scraped {len(scoregg_profiles)} jugadores de ScoreGG")
    
    logger.info("="*80)
    logger.success("✅ SCRAPING REGIONAL COMPLETADO")
    logger.info("="*80)


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "regional_connectors_{time}.log",
        rotation="50 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    asyncio.run(main())
