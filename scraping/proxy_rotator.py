"""
Scraper mejorado con rotación de proxies real usando proxy services
Integración con servicios como Bright Data, ScraperAPI, etc.
"""
import asyncio
import os
from typing import Optional, Dict
from playwright.async_api import async_playwright, Browser, ProxySettings
from loguru import logger


class ProxyRotator:
    """
    Manejador de rotación de proxies
    Soporta múltiples servicios de proxy
    """
    
    def __init__(self, proxy_service: str = "none"):
        """
        Inicializa el rotador de proxies
        
        Args:
            proxy_service: Servicio de proxy a usar
                - "none": Sin proxy
                - "bright_data": Bright Data (Luminati)
                - "scraperapi": ScraperAPI
                - "custom": Lista personalizada
        """
        self.proxy_service = proxy_service
        self.current_proxy_index = 0
        self.proxies = self._load_proxies()
    
    def _load_proxies(self) -> list:
        """Carga la lista de proxies según el servicio configurado"""
        
        if self.proxy_service == "bright_data":
            # Bright Data (Luminati)
            # Formato: http://username-session-{random}:password@proxy.brightdata.com:port
            username = os.getenv("BRIGHT_DATA_USERNAME", "")
            password = os.getenv("BRIGHT_DATA_PASSWORD", "")
            host = os.getenv("BRIGHT_DATA_HOST", "brd.superproxy.io")
            port = os.getenv("BRIGHT_DATA_PORT", "22225")
            
            if username and password:
                return [{
                    "server": f"http://{host}:{port}",
                    "username": username,
                    "password": password
                }]
        
        elif self.proxy_service == "scraperapi":
            # ScraperAPI
            api_key = os.getenv("SCRAPERAPI_KEY", "")
            if api_key:
                return [{
                    "server": f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"
                }]
        
        elif self.proxy_service == "custom":
            # Cargar desde variable de entorno PROXY_LIST
            # Formato: host1:port1:user1:pass1,host2:port2:user2:pass2
            proxy_string = os.getenv("PROXY_LIST", "")
            proxies = []
            
            if proxy_string:
                for proxy in proxy_string.split(","):
                    parts = proxy.strip().split(":")
                    if len(parts) >= 2:
                        proxy_config = {
                            "server": f"http://{parts[0]}:{parts[1]}"
                        }
                        if len(parts) >= 4:
                            proxy_config["username"] = parts[2]
                            proxy_config["password"] = parts[3]
                        proxies.append(proxy_config)
            
            return proxies
        
        # Sin proxies
        return []
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Obtiene el siguiente proxy en rotación
        
        Returns:
            Configuración del proxy o None si no hay proxies
        """
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        return proxy
    
    def has_proxies(self) -> bool:
        """Verifica si hay proxies disponibles"""
        return len(self.proxies) > 0


class StealthBrowser:
    """
    Browser con configuración stealth completa
    Anti-detección avanzada
    """
    
    @staticmethod
    async def create_stealth_browser(
        headless: bool = True,
        proxy: Optional[Dict[str, str]] = None
    ) -> Browser:
        """
        Crea un browser con configuración stealth completa
        
        Args:
            headless: Si debe ejecutarse en modo headless
            proxy: Configuración de proxy opcional
            
        Returns:
            Browser configurado
        """
        playwright = await async_playwright().start()
        
        # Configurar opciones del browser
        launch_options = {
            "headless": headless,
            "args": [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        }
        
        # Añadir proxy si está disponible
        if proxy:
            launch_options["proxy"] = proxy
        
        browser = await playwright.chromium.launch(**launch_options)
        
        return browser
    
    @staticmethod
    async def apply_stealth_scripts(page):
        """
        Aplica scripts anti-detección a una página
        
        Args:
            page: Página de Playwright
        """
        # Script completo anti-detección
        await page.add_init_script("""
            // Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Chrome runtime
            window.navigator.chrome = {
                runtime: {},
            };
            
            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            
            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Ocultar automation
            delete navigator.__proto__.webdriver;
            
            // Mock de conexión
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50
                })
            });
        """)


# Ejemplo de uso con el scraper ninja
async def example_with_proxy():
    """Ejemplo de uso del scraper con proxy rotation"""
    
    # Inicializar rotador de proxies
    proxy_rotator = ProxyRotator(proxy_service="none")  # Cambiar a "bright_data" o "scraperapi"
    
    # Obtener proxy
    proxy = proxy_rotator.get_next_proxy()
    
    # Crear browser stealth
    browser = await StealthBrowser.create_stealth_browser(
        headless=True,
        proxy=proxy
    )
    
    # Crear página
    page = await browser.new_page()
    
    # Aplicar scripts stealth
    await StealthBrowser.apply_stealth_scripts(page)
    
    # Usar la página...
    await page.goto("https://www.cnnbrasil.com.br/esportes/outros-esportes/e-sports/")
    
    # Cerrar
    await browser.close()


if __name__ == "__main__":
    asyncio.run(example_with_proxy())
