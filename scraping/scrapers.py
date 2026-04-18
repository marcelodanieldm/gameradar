"""
Scrapers base y específicos para diferentes fuentes
Motor de ingesta asíncrono con Playwright
"""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import PlayerProfile, GameTitle, CountryCode, Champion, PlayerStats
from core.country_detector import detect_country
from core.config import settings


class BaseScraper(ABC):
    """Clase base para todos los scrapers"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.rate_limit_delay = settings.rate_limit_delay
        
    async def __aenter__(self):
        """Context manager: inicializar browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        logger.info(f"🌐 Browser iniciado para {self.__class__.__name__}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager: cerrar browser"""
        if self.browser:
            await self.browser.close()
            logger.info(f"🌐 Browser cerrado para {self.__class__.__name__}")
    
    async def create_page(self) -> Page:
        """Crea una nueva página con configuración personalizada"""
        page = await self.browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": settings.user_agent,
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,zh;q=0.7"
        })
        return page
    
    @abstractmethod
    async def scrape_player(self, identifier: str) -> Optional[PlayerProfile]:
        """
        Método abstracto para scrapear un jugador
        
        Args:
            identifier: Identificador del jugador (URL, nickname, etc)
            
        Returns:
            PlayerProfile o None si falla
        """
        pass
    
    async def scrape_players(self, identifiers: List[str]) -> List[PlayerProfile]:
        """
        Scrapea múltiples jugadores con rate limiting
        
        Args:
            identifiers: Lista de identificadores
            
        Returns:
            Lista de PlayerProfiles exitosos
        """
        profiles = []
        
        for i, identifier in enumerate(identifiers):
            logger.info(f"📊 Scraping {i+1}/{len(identifiers)}: {identifier}")
            
            try:
                profile = await self.scrape_player(identifier)
                if profile:
                    profiles.append(profile)
                    logger.success(f"✓ {profile.nickname} scraped exitosamente")
            except Exception as e:
                logger.error(f"✗ Error scraping {identifier}: {e}")
            
            # Rate limiting
            if i < len(identifiers) - 1:
                await asyncio.sleep(self.rate_limit_delay)
        
        logger.info(f"🎯 Total scraped: {len(profiles)}/{len(identifiers)}")
        return profiles


class LiquipediaScraper(BaseScraper):
    """Scraper para Liquipedia (India, Vietnam, SEA)"""
    
    BASE_URL = "https://liquipedia.net"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape_player(self, player_url: str) -> Optional[PlayerProfile]:
        """
        Scrapea un jugador de Liquipedia
        
        Args:
            player_url: URL del perfil en Liquipedia
            
        Returns:
            PlayerProfile o None
        """
        page = await self.create_page()
        
        try:
            await page.goto(player_url, wait_until="domcontentloaded")
            
            # Extraer nickname
            nickname_element = await page.query_selector("h1.firstHeading")
            nickname = await nickname_element.inner_text() if nickname_element else "Unknown"
            
            # Extraer país desde bandera
            flag_element = await page.query_selector("span.flag a")
            country_text = await flag_element.get_attribute("title") if flag_element else ""
            
            # Detectar país
            country = detect_country(
                profile_text=country_text,
                url=player_url
            )
            
            # Extraer información del infobox
            infobox = await page.query_selector("div.infobox-center")
            
            # Placeholder para stats (Liquipedia no siempre tiene stats detallados)
            # Aquí deberías implementar la lógica específica según el juego
            stats = PlayerStats(
                win_rate=50.0,  # Placeholder
                kda=2.5,  # Placeholder
                games_analyzed=100
            )
            
            # Placeholder para top champions
            top_champions = [
                Champion(name="Champion 1", games_played=50, win_rate=55.0),
                Champion(name="Champion 2", games_played=30, win_rate=52.0),
                Champion(name="Champion 3", games_played=20, win_rate=48.0),
            ]
            
            # Crear perfil
            profile = PlayerProfile(
                nickname=nickname.strip(),
                game=GameTitle.LEAGUE_OF_LEGENDS,  # Ajustar según contexto
                country=country,
                server="SEA",  # Ajustar según región
                rank="Unknown",  # Liquipedia no siempre tiene rank
                stats=stats,
                top_champions=top_champions,
                profile_url=player_url
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error scraping Liquipedia: {e}")
            return None
        finally:
            await page.close()


class OPGGScraper(BaseScraper):
    """Scraper para OP.GG (Korea, Vietnam)"""
    
    BASE_URL = "https://www.op.gg"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape_player(self, summoner_name: str, region: str = "kr") -> Optional[PlayerProfile]:
        """
        Scrapea un jugador de OP.GG
        
        Args:
            summoner_name: Nombre del invocador
            region: Región (kr, vn, etc)
            
        Returns:
            PlayerProfile o None
        """
        page = await self.create_page()
        
        try:
            # Construir URL (formato actualizado 2026)
            url = f"https://www.op.gg/summoners/{region}/{summoner_name}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Esperar a que cargue el contenido principal (selectores actualizados)
            # Intentar múltiples selectores para mayor robustez
            selectors_to_try = [
                "h1.summoner-name",
                ".profile-icon",
                "[class*='summoner']",
                "h1",
                ".css-"
            ]
            
            loaded = False
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    loaded = True
                    break
                except:
                    continue
            
            if not loaded:
                logger.warning(f"No se pudo cargar la página de {summoner_name}")
                return None
            
            # Extraer nickname - intentar varios selectores
            nickname = summoner_name
            for selector in ["h1", ".name", "[class*='name']", "[class*='summoner']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and text.strip():
                            nickname = text.strip()
                            break
                except:
                    continue
            
            # Extraer rango - intentar varios selectores
            rank = "Unranked"
            for selector in [".tier", "[class*='tier']", "[class*='rank']", ".rank"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and any(r in text for r in ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Challenger"]):
                            rank = text.strip()
                            break
                except:
                    continue
            
            # Extraer win rate
            win_rate = 50.0
            for selector in [".win-rate", "[class*='winrate']", "[class*='win']"]:
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
            
            # Extraer KDA
            kda = 2.0
            for selector in [".kda", "[class*='kda']"]:
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
            
            # Detectar país
            country = detect_country(
                server=region,
                url=url
            )
            
            # Extraer top champions
            champion_elements = await page.query_selector_all(".champion-box")
            top_champions = []
            
            for i, champ_elem in enumerate(champion_elements[:3]):
                champ_name_elem = await champ_elem.query_selector(".champion-name")
                champ_name = await champ_name_elem.inner_text() if champ_name_elem else f"Champion {i+1}"
                
                games_elem = await champ_elem.query_selector(".games")
                games_text = await games_elem.inner_text() if games_elem else "10"
                games = int(games_text.replace("games", "").strip())
                
                champ_wr_elem = await champ_elem.query_selector(".win-rate")
                champ_wr_text = await champ_wr_elem.inner_text() if champ_wr_elem else "50%"
                champ_wr = float(champ_wr_text.replace("%", "").strip())
                
                top_champions.append(Champion(
                    name=champ_name,
                    games_played=games,
                    win_rate=champ_wr
                ))
            
            # Si no hay suficientes champions, agregar placeholders
            while len(top_champions) < 3:
                top_champions.append(Champion(
                    name=f"Champion {len(top_champions)+1}",
                    games_played=0,
                    win_rate=0.0
                ))
            
            # Crear stats
            stats = PlayerStats(
                win_rate=win_rate,
                kda=kda,
                games_analyzed=100
            )
            
            # Crear perfil
            profile = PlayerProfile(
                nickname=nickname.strip(),
                game=GameTitle.LEAGUE_OF_LEGENDS,
                country=country,
                server=region.upper(),
                rank=rank.strip(),
                stats=stats,
                top_champions=top_champions,
                profile_url=url
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error scraping OP.GG: {e}")
            return None
        finally:
            await page.close()


class ScraperFactory:
    """Factory para crear scrapers según la fuente"""
    
    @staticmethod
    def create_scraper(source: str) -> BaseScraper:
        """
        Crea un scraper según la fuente
        
        Args:
            source: Nombre de la fuente (liquipedia, opgg)
            
        Returns:
            Instancia del scraper correspondiente
        """
        scrapers = {
            "liquipedia": LiquipediaScraper,
            "opgg": OPGGScraper,
        }
        
        scraper_class = scrapers.get(source.lower())
        if not scraper_class:
            raise ValueError(f"Scraper '{source}' no soportado. Opciones: {list(scrapers.keys())}")
        
        return scraper_class()


# Función principal de ejemplo
async def main():
    """Ejemplo de uso del scraper"""
    
    # Ejemplo: Scraping de OP.GG Korea
    async with OPGGScraper() as scraper:
        # Lista de jugadores a scrapear
        players = ["Faker", "Chovy", "ShowMaker"]
        
        profiles = []
        for player in players:
            profile = await scraper.scrape_player(player, region="kr")
            if profile:
                profiles.append(profile)
        
        logger.info(f"✓ Scraped {len(profiles)} jugadores exitosamente")
        
        # Mostrar resultados
        for profile in profiles:
            logger.info(
                f"🎮 {profile.nickname} ({profile.country.value}) - "
                f"Rank: {profile.rank} | WR: {profile.stats.win_rate}% | "
                f"KDA: {profile.stats.kda}"
            )


if __name__ == "__main__":
    asyncio.run(main())
