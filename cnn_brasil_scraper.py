"""
CNN Brasil E-sports Scraper - Ninja Mode 🥷
Script rápido y eficiente con proxy rotation y error handling silencioso
"""
import asyncio
import random
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, ProxySettings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime

from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode
from country_detector import detect_country
from supabase_client import SupabaseClient
from config import settings


# Lista de proxies rotativos (añadir proxies reales en producción)
PROXY_LIST = [
    # Free proxies - reemplazar con proxies premium en producción
    {"server": "http://proxy1.example.com:8080"},
    {"server": "http://proxy2.example.com:8080"},
    {"server": "http://proxy3.example.com:8080"},
]

# User agents rotativos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class CNNBrasilNinjaScraper:
    """
    Scraper ninja para CNN Brasil E-sports
    Rápido, eficiente, con proxy rotation y error handling silencioso
    """
    
    TARGET_URL = "https://www.cnnbrasil.com.br/esportes/outros-esportes/e-sports/"
    
    def __init__(self, use_proxies: bool = False):
        """
        Inicializa el scraper ninja
        
        Args:
            use_proxies: Si se debe usar rotación de proxies
        """
        self.use_proxies = use_proxies
        self.db = SupabaseClient()
        self.scraped_count = 0
        self.error_count = 0
        
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Obtiene un proxy aleatorio de la lista"""
        if not self.use_proxies or not PROXY_LIST:
            return None
        return random.choice(PROXY_LIST)
    
    def _get_random_user_agent(self) -> str:
        """Obtiene un user agent aleatorio"""
        return random.choice(USER_AGENTS)
    
    async def _create_stealth_page(self, browser: Browser) -> Page:
        """
        Crea una página con configuración stealth
        
        Args:
            browser: Instancia del browser
            
        Returns:
            Página configurada en modo stealth
        """
        page = await browser.new_page()
        
        # Configurar user agent aleatorio
        await page.set_extra_http_headers({
            "User-Agent": self._get_random_user_agent(),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        })
        
        # Anti-detección: ocultar webdriver
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
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
        """)
        
        return page
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=False  # Ninja mode: no reraise, silent failure
    )
    async def _scrape_player_data(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extrae datos de jugadores de la página de CNN Brasil
        
        Args:
            page: Página de Playwright
            
        Returns:
            Lista de datos de jugadores extraídos
        """
        try:
            # Navegar a la página objetivo
            await page.goto(self.TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Esperar a que cargue el contenido principal
            await page.wait_for_selector("article, .card, .player-card", timeout=10000)
            
            # Extraer artículos/cards de jugadores
            # Nota: Los selectores específicos dependen de la estructura real del sitio
            # Estos son selectores genéricos que deben ajustarse
            
            players_data = []
            
            # Intentar diferentes selectores comunes
            selectors = [
                "article",
                ".card",
                ".player-card",
                ".athlete-card",
                ".esports-player",
                "[data-player]",
            ]
            
            elements = None
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        break
                except:
                    continue
            
            if not elements:
                # Si no encuentra elementos, extraer del texto completo
                content = await page.content()
                logger.warning("⚠ No se encontraron elementos específicos, extrayendo del contenido general")
                return []
            
            # Limitar a top 100
            elements = elements[:100]
            
            for idx, element in enumerate(elements):
                try:
                    # Extraer texto del elemento
                    text = await element.inner_text()
                    
                    # Buscar patrones comunes
                    # Esto es genérico y debe ajustarse según la estructura real
                    
                    # Extraer nickname (primera línea o texto más destacado)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    nickname = lines[0] if lines else f"Player_{idx+1}"
                    
                    # Detectar país desde el texto
                    country = detect_country(
                        profile_text=text,
                        url=self.TARGET_URL
                    )
                    
                    # Extraer stats si están disponibles
                    # Buscar números que puedan ser win rate o KDA
                    import re
                    numbers = re.findall(r'\d+\.?\d*', text)
                    
                    win_rate = float(numbers[0]) if len(numbers) > 0 else 50.0
                    kda = float(numbers[1]) if len(numbers) > 1 else 2.0
                    
                    # Asegurar que win_rate esté en rango válido
                    if win_rate > 100:
                        win_rate = 50.0
                    
                    # Extraer enlace del perfil
                    link_element = await element.query_selector("a")
                    profile_url = await link_element.get_attribute("href") if link_element else self.TARGET_URL
                    
                    # Asegurar URL completa
                    if profile_url and not profile_url.startswith("http"):
                        profile_url = f"https://www.cnnbrasil.com.br{profile_url}"
                    
                    player_data = {
                        "nickname": nickname[:100],  # Limitar a 100 caracteres
                        "game": "ESPORTS",  # Genérico
                        "country": country.value,
                        "server": "BR",
                        "rank": "Unknown",
                        "win_rate": min(max(win_rate, 0), 100),  # Clamp entre 0-100
                        "kda": max(kda, 0),
                        "profile_url": profile_url or self.TARGET_URL,
                        "source": "cnn_brasil",
                    }
                    
                    players_data.append(player_data)
                    
                except Exception as e:
                    # Ninja mode: silent error, continue
                    logger.debug(f"Error extrayendo jugador {idx}: {e}")
                    continue
            
            return players_data
            
        except Exception as e:
            # Ninja mode: log pero no fallar
            logger.debug(f"Error en scraping: {e}")
            return []
    
    async def _upsert_player_to_supabase(self, player_data: Dict[str, Any]) -> bool:
        """
        Hace upsert de un jugador en Supabase
        Si es de India, añade tag 'Region: India'
        
        Args:
            player_data: Datos del jugador
            
        Returns:
            True si tuvo éxito, False si falló
        """
        try:
            # Añadir tag de región para jugadores de India
            tags = []
            if player_data["country"] == "IN":
                tags.append("Region: India")
            
            # Crear registro Bronze con tags
            raw_data = {
                **player_data,
                "tags": tags,
                "scraped_at": datetime.utcnow().isoformat(),
            }
            
            # Insertar en Bronze (trigger automático normaliza a Silver)
            self.db.insert_bronze_raw(
                raw_data=raw_data,
                source="cnn_brasil",
                source_url=player_data.get("profile_url", self.TARGET_URL)
            )
            
            self.scraped_count += 1
            return True
            
        except Exception as e:
            # Ninja mode: silent error
            logger.debug(f"Error en upsert: {e}")
            self.error_count += 1
            return False
    
    async def run_ninja_scrape(self) -> Dict[str, int]:
        """
        Ejecuta el scraping ninja completo
        
        Returns:
            Diccionario con estadísticas de ejecución
        """
        logger.info("🥷 Iniciando scraping ninja de CNN Brasil...")
        
        start_time = datetime.utcnow()
        
        try:
            # Configurar proxy si está habilitado
            proxy = self._get_random_proxy()
            
            playwright = await async_playwright().start()
            
            # Lanzar browser
            browser = await playwright.chromium.launch(
                headless=True,
                proxy=proxy
            )
            
            # Crear página stealth
            page = await self._create_stealth_page(browser)
            
            # Scraping de datos
            players_data = await self._scrape_player_data(page)
            
            # Cerrar browser
            await browser.close()
            await playwright.stop()
            
            logger.info(f"✓ Extraídos {len(players_data)} jugadores")
            
            # Upsert en Supabase
            for player_data in players_data:
                await self._upsert_player_to_supabase(player_data)
                
                # Mini delay entre upserts
                await asyncio.sleep(0.1)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            stats = {
                "scraped": self.scraped_count,
                "errors": self.error_count,
                "duration_seconds": round(duration, 2),
            }
            
            logger.success(
                f"🥷 Scraping ninja completado: "
                f"{stats['scraped']} insertados, "
                f"{stats['errors']} errores, "
                f"{stats['duration_seconds']}s"
            )
            
            return stats
            
        except Exception as e:
            # Ninja mode: log minimal y continuar
            logger.error(f"✗ Error crítico en scraping: {e}")
            return {
                "scraped": self.scraped_count,
                "errors": self.error_count + 1,
                "duration_seconds": 0,
            }


# Función principal para GitHub Actions
async def main():
    """Función principal para ejecutar desde GitHub Actions"""
    
    # Configurar logging silencioso (solo errores críticos)
    logger.remove()
    logger.add(
        "ninja_scraper.log",
        level="ERROR",
        rotation="1 MB",
        compression="zip"
    )
    
    # Ejecutar scraper ninja
    scraper = CNNBrasilNinjaScraper(use_proxies=False)  # Cambiar a True si hay proxies
    stats = await scraper.run_ninja_scrape()
    
    # Output para GitHub Actions
    print(f"::set-output name=scraped::{stats['scraped']}")
    print(f"::set-output name=errors::{stats['errors']}")
    print(f"::set-output name=duration::{stats['duration_seconds']}")
    
    # Exit code basado en resultados
    if stats['scraped'] > 0:
        exit(0)  # Éxito
    else:
        exit(1)  # Fallo


if __name__ == "__main__":
    asyncio.run(main())
