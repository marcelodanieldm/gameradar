"""
Script de Ingesta de Datos - Capa Bronze
Scrapea rankings de e-sports y los inserta en bronze_raw_data

Características:
- Playwright para scraping asíncrono
- Soporte para caracteres asiáticos (Coreano/Chino/Japonés)
- Detección automática de encoding Unicode
- Manejo robusto de errores (no se detiene si falta un dato)
- Integración directa con Supabase Bronze layer
- Técnicas avanzadas anti-detección para evitar bloqueos
"""
import asyncio
import re
import random
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from loguru import logger
from datetime import datetime, timezone

from supabase_client import SupabaseClient
from country_detector import detect_country, CountryCode
from models import GameTitle
from config import settings


class BronzeIngestionScraper:
    """
    Scraper robusto para ingesta de datos en capa Bronze
    Diseñado para manejar múltiples fuentes y caracteres asiáticos
    Incluye técnicas anti-detección avanzadas
    """
    
    # User-Agents realistas para rotar
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    
    def __init__(self, region: str = "KR", headless: bool = True):
        """
        Inicializa el scraper de ingesta
        
        Args:
            region: Región objetivo ('KR', 'IN', 'CN', 'VN', etc.)
            headless: Si True, ejecuta browser en modo headless (sin GUI)
                     Si False, muestra el browser (menos detectable pero más lento)
        """
        self.region = region.upper()
        self.headless = headless
        self.supabase = SupabaseClient()
        self.browser: Optional[Browser] = None
        self.scraped_count = 0
        self.error_count = 0
        self.user_agent = random.choice(self.USER_AGENTS)
        
        logger.info(f"🎯 Scraper de ingesta Bronze inicializado para región: {self.region}")
        if not headless:
            logger.warning("⚠ Modo NO-HEADLESS activado - el browser será visible")
    
    async def __aenter__(self):
        """Context manager: inicializar browser con configuración stealth"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,  # Configurable: False para bypassear WAF
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized'
            ]
        )
        mode_text = "headless" if self.headless else "visible"
        logger.info(f"🌐 Browser iniciado en modo {mode_text} con configuración anti-detección")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager: cerrar browser"""
        if self.browser:
            await self.browser.close()
            logger.info(f"🌐 Browser cerrado | Scraped: {self.scraped_count} | Errors: {self.error_count}")
    
    async def setup_stealth_page(self, page: Page) -> None:
        """
        Configura una página con técnicas anti-detección avanzadas
        
        Args:
            page: Página de Playwright a configurar
        """
        # 1. User-Agent realista
        await page.set_extra_http_headers({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
        
        # 2. Viewport aleatorio (simular diferentes dispositivos)
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900}
        ]
        await page.set_viewport_size(random.choice(viewports))
        
        # 3. JavaScript para ocultar automatización
        await page.add_init_script("""
            // Sobrescribir webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Sobrescribir plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Sobrescribir languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'ko']
            });
            
            // Chrome específico
            window.chrome = {
                runtime: {}
            };
            
            // Permisos
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        logger.debug("✅ Página configurada con protección anti-detección")
    
    async def establish_session(self, page: Page, base_url: str) -> None:
        """
        Establece una sesión previa visitando la página principal
        Esto ayuda a obtener cookies legítimas y reducir detección
        
        Args:
            page: Página de Playwright
            base_url: URL base del sitio (ej: "https://op.gg")
        """
        try:
            logger.debug(f"🍪 Estableciendo sesión previa en {base_url}...")
            
            # Visitar homepage
            await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            
            # Simular lectura natural
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            # Scroll aleatorio
            for _ in range(2):
                scroll_amount = random.randint(200, 500)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount});")
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Click en algún elemento visible (si existe)
            try:
                await page.click("a", timeout=2000)
                await asyncio.sleep(random.uniform(1.0, 2.0))
            except:
                pass  # No hay problema si no hay links
            
            logger.debug("✅ Sesión establecida con cookies")
            
        except Exception as e:
            logger.debug(f"⚠ No se pudo establecer sesión previa: {e}")
    
    def detect_asian_characters(self, text: str) -> Dict[str, bool]:
        """
        Detecta si el texto contiene caracteres asiáticos
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con flags para cada tipo de caracteres
        """
        # Rangos Unicode para caracteres asiáticos
        korean_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]')  # Hangul
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')  # CJK Unified
        japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')  # Hiragana + Katakana
        
        return {
            "has_korean": bool(korean_pattern.search(text)),
            "has_chinese": bool(chinese_pattern.search(text)),
            "has_japanese": bool(japanese_pattern.search(text)),
            "has_asian": bool(korean_pattern.search(text) or 
                            chinese_pattern.search(text) or 
                            japanese_pattern.search(text))
        }
    
    def safe_extract_text(self, element, default: str = "") -> str:
        """
        Extrae texto de un elemento de forma segura
        
        Args:
            element: Elemento Playwright
            default: Valor por defecto si falla
            
        Returns:
            Texto extraído o valor por defecto
        """
        try:
            if element:
                return element.strip()
            return default
        except Exception as e:
            logger.debug(f"Error extrayendo texto: {e}")
            return default
    
    async def scrape_liquipedia_ranking(
        self, 
        game: str = "leagueoflegends",
        ranking_page: str = "Portal:Players"
    ) -> List[Dict[str, Any]]:
        """
        Scrapea ranking de Liquipedia
        
        Args:
            game: Nombre del juego en Liquipedia
            ranking_page: Página de ranking específica
            
        Returns:
            Lista de datos crudos de jugadores
        """
        url = f"https://liquipedia.net/{game}/{ranking_page}"
        logger.info(f"📄 Scraping Liquipedia: {url}")
        
        players_data = []
        page = await self.browser.new_page()
        
        try:
            # Navegar a la página
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Esperar a que cargue contenido dinámico
            
            # Buscar tabla de jugadores (Liquipedia usa wikitable)
            tables = await page.query_selector_all("table.wikitable")
            
            if not tables:
                logger.warning("⚠ No se encontraron tablas en Liquipedia")
                return players_data
            
            # Procesar primera tabla encontrada
            table = tables[0]
            rows = await table.query_selector_all("tr")
            
            logger.info(f"📊 Procesando {len(rows)} filas de la tabla")
            
            for i, row in enumerate(rows[1:], 1):  # Skip header row
                try:
                    cells = await row.query_selector_all("td")
                    
                    if len(cells) < 2:
                        continue
                    
                    # Extraer datos (orden puede variar según la tabla)
                    player_data = await self._extract_player_from_cells(cells, url)
                    
                    if player_data:
                        # Detectar caracteres asiáticos
                        char_info = self.detect_asian_characters(
                            player_data.get("nickname", "")
                        )
                        player_data["character_detection"] = char_info
                        
                        players_data.append(player_data)
                        self.scraped_count += 1
                        
                        if i % 10 == 0:
                            logger.info(f"  ⏳ Procesados {i} jugadores...")
                
                except Exception as e:
                    self.error_count += 1
                    logger.debug(f"⚠ Error procesando fila {i}: {e}")
                    # NO detenerse, continuar con siguiente jugador
                    continue
            
            logger.success(f"✓ Scraped {len(players_data)} jugadores de Liquipedia")
            
        except PlaywrightTimeout:
            logger.error(f"⏱ Timeout cargando {url}")
        except Exception as e:
            logger.error(f"❌ Error scraping Liquipedia: {e}")
        finally:
            await page.close()
        
        return players_data
    
    async def _extract_player_from_cells(
        self, 
        cells, 
        source_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extrae información de jugador desde celdas de tabla
        
        Args:
            cells: Lista de celdas de la fila
            source_url: URL de origen
            
        Returns:
            Dict con datos del jugador o None
        """
        try:
            # Estructura común en Liquipedia: ID | Nombre | País | Team | etc
            player_id = ""
            nickname = ""
            rank = ""
            team = ""
            country = ""
            
            # Intentar extraer ID y nickname (varía según tabla)
            if len(cells) >= 1:
                # Primera celda suele tener ID o nickname
                cell_text = await cells[0].inner_text()
                nickname = self.safe_extract_text(cell_text, f"Player_{self.scraped_count}")
            
            if len(cells) >= 2:
                # Segunda celda puede tener nombre completo o ID
                cell_text = await cells[1].inner_text()
                if cell_text.strip():
                    player_id = self.safe_extract_text(cell_text)
            
            # Buscar banderas de país
            for cell in cells[:5]:  # Revisar primeras 5 celdas
                flag_img = await cell.query_selector("img[alt*='flag']")
                if flag_img:
                    alt_text = await flag_img.get_attribute("alt")
                    if alt_text:
                        country = alt_text
                        break
            
            # Extraer team (suele estar en celdas posteriores)
            if len(cells) >= 3:
                team_cell = await cells[2].inner_text()
                team = self.safe_extract_text(team_cell)
            
            # Detectar país desde múltiples fuentes
            detected_country = detect_country(
                profile_text=f"{nickname} {country}",
                server=self.region.lower(),
                url=source_url
            )
            
            # Crear registro crudo
            raw_data = {
                "nickname": nickname,
                "player_id": player_id or nickname,
                "region": self.region,
                "country": detected_country.value,
                "rank": rank,
                "team": team,
                "game": "LOL",  # Ajustar según contexto
                "server": self.region,
                "profile_url": source_url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "liquipedia",
                # Metadatos adicionales
                "raw_country_text": country,
                "has_asian_characters": self.detect_asian_characters(nickname)["has_asian"]
            }
            
            return raw_data
            
        except Exception as e:
            logger.debug(f"Error extrayendo jugador: {e}")
            return None
    
    async def scrape_opgg_ranking(
        self,
        game: str = "lol",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrapea ranking de OP.GG
        
        Args:
            game: Juego (lol, val)
            limit: Número máximo de jugadores a scrapear
            
        Returns:
            Lista de datos crudos de jugadores
        """
        region_code = self.region.lower()
        url = f"https://{region_code}.op.gg/leaderboards/tier?region={region_code}"
        
        logger.info(f"📄 Scraping OP.GG: {url}")
        
        players_data = []
        page = await self.browser.new_page()
        
        try:
            # Configurar página con stealth
            await self.setup_stealth_page(page)
            
            # WORKAROUND: Establecer sesión previa para obtener cookies legítimas
            # Esto reduce la probabilidad de 403 Error de WAF
            try:
                await self.establish_session(page, f"https://{region_code}.op.gg")
            except Exception as e:
                logger.debug(f"⚠ Sesión previa falló, continuando: {e}")
            
            # Navegar con delays aleatorios
            logger.debug(f"🔗 Navegando a leaderboards...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Delay aleatorio LARGO para OP.GG (5-10 segundos) - evitar detección WAF
            logger.debug(f"⏱ Delay largo (5-10s) para evitar detección...")
            await asyncio.sleep(random.uniform(5.0, 10.0))
            
            # Scroll aleatorio (simular lectura)
            await page.evaluate("window.scrollTo(0, Math.random() * 500);")
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Esperar a que cargue contenido dinámico
            await page.wait_for_timeout(2000)
            
            # OP.GG usa estructura de tabla dinámica
            # Selector puede variar - ajustar según UI actual
            # Intentar múltiples selectores de fallback
            player_rows = await page.query_selector_all("[data-summoner-id]")
            
            if not player_rows:
                player_rows = await page.query_selector_all("tr.ranked-player")
            
            if not player_rows:
                # Más fallbacks para diferentes versiones de OP.GG
                player_rows = await page.query_selector_all("table tbody tr")
            
            if not player_rows:
                # Último intento: buscar por estructura CSS común
                player_rows = await page.query_selector_all(".leaderboard-row, .player-row, .summoner-row")
            
            logger.info(f"📊 Encontrados {len(player_rows)} jugadores en OP.GG")
            
            for i, row in enumerate(player_rows[:limit], 1):
                try:
                    # Delay aleatorio entre jugadores (0.3-0.8s) para parecer humano
                    if i > 1:
                        await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                    # Extraer nickname con múltiples selectores de fallback
                    nickname = ""
                    for selector in [".summoner-name", ".player-name", ".name", "a[href*='summoner']"]:
                        nickname_elem = await row.query_selector(selector)
                        if nickname_elem:
                            nickname = await nickname_elem.inner_text()
                            break
                    
                    # Extraer rank con múltiples selectores
                    rank = ""
                    for selector in [".tier", ".rank", ".rating", "[class*='tier']"]:
                        rank_elem = await row.query_selector(selector)
                        if rank_elem:
                            rank = await rank_elem.inner_text()
                            break
                    
                    # Extraer LP (League Points)
                    lp = ""
                    for selector in [".lp", ".points", ".league-points", "[class*='lp']"]:
                        lp_elem = await row.query_selector(selector)
                        if lp_elem:
                            lp = await lp_elem.inner_text()
                            break
                    
                    # Crear registro crudo
                    raw_data = {
                        "nickname": self.safe_extract_text(nickname, f"Player_{i}"),
                        "player_id": self.safe_extract_text(nickname),
                        "region": self.region,
                        "country": self.region,  # OP.GG es por servidor
                        "rank": self.safe_extract_text(rank),
                        "lp": self.safe_extract_text(lp),
                        "game": "LOL",
                        "server": self.region,
                        "profile_url": url,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "data_source": "opgg",
                        "has_asian_characters": self.detect_asian_characters(nickname)["has_asian"]
                    }
                    
                    players_data.append(raw_data)
                    self.scraped_count += 1
                    
                    # Log cada 5 jugadores para monitoreo
                    if i % 5 == 0:
                        logger.debug(f"   Procesados {i}/{min(limit, len(player_rows))} jugadores...")
                    
                    # Scroll aleatorio cada 10 jugadores (simular lectura natural)
                    if i % 10 == 0:
                        scroll_amount = random.randint(100, 300)
                        await page.evaluate(f"window.scrollBy(0, {scroll_amount});")
                        await asyncio.sleep(random.uniform(0.2, 0.5))
                    
                except Exception as e:
                    self.error_count += 1
                    logger.debug(f"⚠ Error procesando jugador {i}: {e}")
                    continue
            
            if len(players_data) > 0:
                logger.success(f"✓ Scraped {len(players_data)} jugadores de OP.GG")
            else:
                logger.warning("⚠ No se encontraron jugadores. Posible cambio en estructura HTML o bloqueo anti-bot")
            
        except Exception as e:
            logger.error(f"❌ Error scraping OP.GG: {e}")
            logger.debug(f"   URL: {url}")
            logger.debug(f"   User-Agent: {self.user_agent}")
        finally:
            await page.close()
        
        # 🔄 FALLBACK AUTOMÁTICO: Si scraping falló, usar Riot Games Official API
        if len(players_data) == 0:
            logger.info("🔄 Activando fallback: Riot Games Official API...")
            players_data = await self._fallback_riot_api(game, limit)
        
        return players_data
    
    async def _fallback_riot_api(self, game: str = "lol", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fallback GRATUITO: Usa Riot Games Official API cuando scraping falla
        
        Args:
            game: Juego (actualmente solo 'lol')
            limit: Número de jugadores a obtener
            
        Returns:
            Lista de datos crudos en formato compatible con bronze_raw_data
        """
        if game != "lol":
            logger.warning(f"⚠️ Riot API solo soporta LoL actualmente (solicitado: {game})")
            return []
        
        # Verificar API key
        api_key = settings.riot_api_key
        if not api_key or api_key == "your-riot-api-key-here":
            logger.warning("⚠️ RIOT_API_KEY no configurada - fallback no disponible")
            logger.info("💡 Configura RIOT_API_KEY en .env para usar fallback automático")
            logger.info("   Obtén tu API key gratis en: https://developer.riotgames.com/")
            return []
        
        try:
            # Import dinámico para evitar dependencias circulares
            from riot_api_client import fetch_players_from_riot_api
            
            logger.info(f"🎮 Obteniendo jugadores desde Riot API (región: {self.region})...")
            players = await fetch_players_from_riot_api(
                region=self.region,
                api_key=api_key,
                limit=limit
            )
            
            if not players:
                logger.warning("⚠️ Riot API no retornó jugadores")
                return []
            
            # Convertir PlayerProfile a formato de bronze_raw_data
            players_data = []
            for player in players:
                raw_data = {
                    "nickname": player.player_name,
                    "player_id": player.player_name,
                    "region": player.region,
                    "country": player.region,
                    "rank": f"{player.tier} #{player.rank}",
                    "lp": str(player.lp),
                    "win_rate": f"{player.win_rate}%",
                    "games_played": str(player.games_played),
                    "game": "LOL",
                    "server": player.region,
                    "profile_url": player.source_url,
                    "scraped_at": player.scraped_at.isoformat(),
                    "data_source": "riot_api",
                    "has_asian_characters": self.detect_asian_characters(player.player_name)["has_asian"]
                }
                players_data.append(raw_data)
                self.scraped_count += 1
            
            logger.success(f"✅ {len(players_data)} jugadores obtenidos desde Riot API (fallback)")
            return players_data
        
        except ImportError:
            logger.error("❌ No se pudo importar riot_api_client")
            return []
        
        except Exception as e:
            logger.error(f"❌ Error en fallback de Riot API: {e}")
            return []
    
    def insert_to_bronze(self, players_data: List[Dict[str, Any]]) -> int:
        """
        Inserta datos crudos en la capa Bronze de Supabase
        
        Args:
            players_data: Lista de datos de jugadores
            
        Returns:
            Número de registros insertados exitosamente
        """
        inserted_count = 0
        
        logger.info(f"💾 Insertando {len(players_data)} registros en Bronze...")
        
        for i, player in enumerate(players_data, 1):
            try:
                # Insertar en bronze_raw_data
                # El trigger automáticamente normalizará a Silver
                self.supabase.insert_bronze_raw(
                    raw_data=player,
                    source=player.get("data_source", "unknown"),
                    source_url=player.get("profile_url", "")
                )
                
                inserted_count += 1
                
                if i % 20 == 0:
                    logger.info(f"  ⏳ Insertados {i}/{len(players_data)} registros...")
                
            except Exception as e:
                self.error_count += 1
                logger.warning(f"⚠ Error insertando jugador {player.get('nickname')}: {e}")
                # NO detenerse, continuar con siguiente
                continue
        
        logger.success(f"✓ Insertados {inserted_count}/{len(players_data)} registros en Bronze")
        return inserted_count
    
    async def run_ingestion(
        self,
        source: str = "liquipedia",
        game: str = "leagueoflegends",
        limit: int = 100
    ):
        """
        Ejecuta el flujo completo de ingesta
        
        Args:
            source: Fuente de datos (liquipedia, opgg)
            game: Juego objetivo
            limit: Límite de jugadores a scrapear
        """
        logger.info("="*60)
        logger.info(f"🚀 INICIANDO INGESTA BRONZE")
        logger.info(f"   Region: {self.region}")
        logger.info(f"   Source: {source}")
        logger.info(f"   Game: {game}")
        logger.info("="*60)
        
        try:
            # Scraping según fuente
            if source.lower() == "liquipedia":
                players_data = await self.scrape_liquipedia_ranking(
                    game=game,
                    ranking_page="Portal:Players"
                )
            elif source.lower() == "opgg":
                players_data = await self.scrape_opgg_ranking(
                    game=game,
                    limit=limit
                )
            else:
                raise ValueError(f"Fuente no soportada: {source}")
            
            if not players_data:
                logger.warning("⚠ No se encontraron datos para insertar")
                return
            
            # Mostrar muestra de datos
            logger.info(f"\n📋 Muestra de datos scraped:")
            for player in players_data[:3]:
                asian_flag = "🌏" if player.get("has_asian_characters") else ""
                logger.info(f"  {asian_flag} {player['nickname']} | {player['rank']} | {player['country']}")
            
            # Insertar en Bronze
            inserted = self.insert_to_bronze(players_data)
            
            # Resumen final
            logger.info("\n" + "="*60)
            logger.success("✅ INGESTA COMPLETADA")
            logger.info(f"📊 Resumen:")
            logger.info(f"  - Scraped: {self.scraped_count}")
            logger.info(f"  - Insertados en Bronze: {inserted}")
            logger.info(f"  - Errores (no críticos): {self.error_count}")
            logger.info(f"  - Tasa de éxito: {(inserted/len(players_data)*100):.1f}%")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Error en ingesta: {e}")
            raise


# Función principal para ejecutar el scraper
async def main():
    """
    Función principal - Ejecuta la ingesta de datos
    """
    # Configuración
    REGION = "KR"  # Cambiar según necesidad: KR, IN, VN, CN, etc.
    SOURCE = "liquipedia"  # liquipedia o opgg
    GAME = "leagueoflegends"
    LIMIT = 50  # Número de jugadores a scrapear
    
    # Ejecutar ingesta
    async with BronzeIngestionScraper(region=REGION) as scraper:
        await scraper.run_ingestion(
            source=SOURCE,
            game=GAME,
            limit=LIMIT
        )


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "bronze_ingestion.log",
        rotation="10 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    # Ejecutar
    asyncio.run(main())
