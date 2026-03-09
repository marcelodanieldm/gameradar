"""
Demo: Usar Proxies Gratuitos con Bronze Ingestion
Combina NO-HEADLESS + Proxies Gratuitos + Delays largos

Solución 100% GRATUITA para bypass de OP.GG WAF
"""
import asyncio
from free_proxy_fetcher import FreeProxyFetcher
from playwright.async_api import async_playwright
from loguru import logger


async def demo_with_free_proxy():
    """
    Demuestra cómo usar proxies gratuitos con Playwright
    para bypassear el WAF de OP.GG
    """
    # 1. Obtener proxies gratuitos validados
    logger.info("=" * 60)
    logger.info("🆓 SOLUCIÓN GRATUITA: Proxies + NO-HEADLESS")
    logger.info("=" * 60)
    
    fetcher = FreeProxyFetcher()
    logger.info("\n📡 Obteniendo proxies gratuitos...")
    working_proxies = await fetcher.get_working_proxies(max_proxies=3)
    
    if not working_proxies:
        logger.error("❌ No se encontraron proxies funcionales")
        logger.info("💡 Intentar de nuevo o usar modo NO-HEADLESS sin proxy")
        return
    
    logger.info(f"✅ {len(working_proxies)} proxies funcionales encontrados\n")
    
    # 2. Probar cada proxy con Playwright
    for i, proxy in enumerate(working_proxies, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Intento {i}/{len(working_proxies)} - Proxy: {proxy}")
        logger.info(f"{'='*60}")
        
        try:
            async with async_playwright() as p:
                # Configurar proxy
                browser = await p.chromium.launch(
                    headless=False,  # NO-HEADLESS = menos detectable
                    proxy={"server": proxy},
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                    ]
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                
                # Verificar IP del proxy
                logger.info("🔍 Verificando IP del proxy...")
                await page.goto("https://api.ipify.org?format=json", timeout=30000)
                ip_info = await page.text_content("body")
                logger.info(f"📍 IP actual: {ip_info}")
                
                # Probar scraping de OP.GG
                logger.info("\n🎯 Probando scraping de OP.GG...")
                url = "https://kr.op.gg/leaderboards/tier?region=kr"
                
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Delay largo (5-10 segundos)
                logger.info("⏱ Esperando 8 segundos (simular humano)...")
                await asyncio.sleep(8)
                
                # Verificar si cargó contenido
                content = await page.content()
                
                if "403 ERROR" in content or "Request blocked" in content:
                    logger.warning(f"⚠️ Proxy {proxy} bloqueado por WAF")
                    await browser.close()
                    continue
                
                if "<html" not in content.lower():
                    logger.warning(f"⚠️ Proxy {proxy} no retornó HTML válido")
                    await browser.close()
                    continue
                
                # Intentar extraer jugadores
                player_elements = await page.query_selector_all("[data-summoner-id]")
                logger.info(f"📊 Elementos encontrados: {len(player_elements)}")
                
                if len(player_elements) > 0:
                    logger.success(f"\n✅ ¡ÉXITO! Proxy {proxy} funcionó")
                    logger.success(f"🎉 Se encontraron {len(player_elements)} jugadores")
                    
                    # Mostrar primeros 3
                    for j, elem in enumerate(player_elements[:3], 1):
                        text = await elem.text_content()
                        logger.info(f"  {j}. {text[:100]}")
                    
                    await browser.close()
                    return True
                else:
                    logger.warning(f"⚠️ No se encontraron jugadores (posible cambio en HTML)")
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ Error con proxy {proxy}: {e}")
            continue
    
    logger.warning("\n⚠️ Todos los proxies fallaron")
    logger.info("\n💡 ALTERNATIVAS GRATUITAS:")
    logger.info("   1. Probar más tarde (proxies rotan)")
    logger.info("   2. Usar Tor Network (más lento pero anónimo)")
    logger.info("   3. Solo NO-HEADLESS sin proxy (70% efectividad)")
    logger.info("   4. Riot Games Official API (gratis con rate limits)")
    
    return False


async def demo_no_headless_only():
    """
    Demuestra modo NO-HEADLESS sin proxies
    Solución más simple y a veces suficiente
    """
    logger.info("\n" + "=" * 60)
    logger.info("🆓 MODO NO-HEADLESS (Sin Proxies)")
    logger.info("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Navegador visible
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        logger.info("🎯 Navegando a OP.GG...")
        url = "https://kr.op.gg/leaderboards/tier?region=kr"
        await page.goto(url, wait_until="domcontentloaded")
        
        logger.info("⏱ Esperando 10 segundos...")
        await asyncio.sleep(10)
        
        # Verificar contenido
        content = await page.content()
        
        if "403 ERROR" in content:
            logger.warning("❌ Bloqueado por WAF incluso en modo NO-HEADLESS")
        else:
            player_elements = await page.query_selector_all("[data-summoner-id]")
            logger.info(f"📊 Jugadores encontrados: {len(player_elements)}")
            
            if len(player_elements) > 0:
                logger.success("✅ ¡Éxito con modo NO-HEADLESS!")
        
        await browser.close()


async def main():
    """Ejecutar demos"""
    logger.info("\n🚀 DEMOS DE SOLUCIONES GRATUITAS PARA OP.GG WAF\n")
    
    # Demo 1: Proxies + NO-HEADLESS (máxima efectividad)
    success = await demo_with_free_proxy()
    
    if not success:
        # Demo 2: Solo NO-HEADLESS (más simple)
        logger.info("\n" + "="*60)
        logger.info("Probando solución alternativa...")
        logger.info("="*60)
        await demo_no_headless_only()
    
    logger.info("\n" + "="*60)
    logger.info("📚 Documentación completa: FREE_SOLUTIONS.md")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
