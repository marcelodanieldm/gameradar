"""
Free Proxy Fetcher - Solución gratuita para bypass de WAF
Obtiene proxies gratuitos de fuentes públicas y los valida

FUENTES GRATUITAS:
1. ProxyScrape API (sin registro)
2. Free-Proxy-List.net
3. ProxyNova
"""
import aiohttp
import asyncio
from typing import List, Optional, Dict
from loguru import logger


class FreeProxyFetcher:
    """Obtiene y valida proxies gratuitos de APIs públicas"""
    
    # APIs públicas sin registro (múltiples fuentes de backup)
    PROXY_SOURCES = [
        # ProxyScrape - Confiable pero con rate limits
        "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        # Proxy-List
        "https://www.proxy-list.download/api/v1/get?type=http",
        # GitHub proxy lists (actualizadas diariamente)
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ]
    
    def __init__(self):
        self.proxies: List[str] = []
        self.validated_proxies: List[str] = []
    
    async def fetch_proxies(self) -> List[str]:
        """
        Obtiene proxies de fuentes gratuitas
        
        Returns:
            Lista de proxies en formato "http://IP:PORT"
        """
        proxies = []
        
        async with aiohttp.ClientSession() as session:
            for source in self.PROXY_SOURCES:
                try:
                    logger.debug(f"🔍 Obteniendo proxies de: {source[:50]}...")
                    async with session.get(source, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            text = await response.text()
                            # Parsear líneas con formato IP:PORT
                            lines = text.strip().split('\n')
                            for line in lines:
                                line = line.strip()
                                if ':' in line and len(line) < 30:  # Validación básica
                                    proxies.append(f"http://{line}")
                            
                            logger.info(f"✅ Obtenidos {len(lines)} proxies de {source[:30]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠ Error obteniendo proxies de {source[:30]}: {e}")
        
        self.proxies = proxies
        logger.info(f"📊 Total proxies gratuitos obtenidos: {len(proxies)}")
        return proxies
    
    async def validate_proxy(self, proxy: str, test_url: str = "http://httpbin.org/ip") -> bool:
        """
        Valida si un proxy funciona
        
        Args:
            proxy: Proxy en formato "http://IP:PORT"
            test_url: URL para testear el proxy
            
        Returns:
            True si el proxy funciona
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_working_proxies(self, max_proxies: int = 10) -> List[str]:
        """
        Obtiene proxies gratuitos validados
        
        Args:
            max_proxies: Número máximo de proxies a validar
            
        Returns:
            Lista de proxies funcionales
        """
        if not self.proxies:
            await self.fetch_proxies()
        
        logger.info(f"🔍 Validando primeros {max_proxies} proxies...")
        
        # Validar en paralelo
        validation_tasks = [
            self.validate_proxy(proxy)
            for proxy in self.proxies[:max_proxies * 3]  # Probar 3x porque muchos fallan
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        self.validated_proxies = [
            proxy for proxy, is_valid in zip(self.proxies[:max_proxies * 3], results)
            if is_valid is True
        ][:max_proxies]
        
        logger.info(f"✅ Proxies funcionales: {len(self.validated_proxies)}/{max_proxies}")
        return self.validated_proxies
    
    def get_random_proxy(self) -> Optional[str]:
        """Obtiene un proxy aleatorio de los validados"""
        if not self.validated_proxies:
            logger.warning("⚠ No hay proxies validados disponibles")
            return None
        
        import random
        return random.choice(self.validated_proxies)


# Ejemplo de uso
async def main():
    """Demostración de uso"""
    fetcher = FreeProxyFetcher()
    
    # Obtener proxies
    proxies = await fetcher.fetch_proxies()
    print(f"\n📊 Proxies obtenidos: {len(proxies)}")
    print(f"Primeros 5: {proxies[:5]}")
    
    # Validar proxies
    working = await fetcher.get_working_proxies(max_proxies=5)
    print(f"\n✅ Proxies funcionales: {len(working)}")
    for proxy in working:
        print(f"  - {proxy}")
    
    # Usar uno aleatorio
    proxy = fetcher.get_random_proxy()
    print(f"\n🎲 Proxy aleatorio: {proxy}")


if __name__ == "__main__":
    asyncio.run(main())
