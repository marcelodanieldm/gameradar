"""
Script de debug para investigar estructura de OP.GG
Captura screenshots y HTML para análisis
"""
import asyncio
from bronze_ingestion import BronzeIngestionScraper
from loguru import logger

async def debug_opgg():
    """Investiga estructura de OP.GG"""
    logger.info("🔍 Iniciando análisis de OP.GG...")
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        page = await scraper.browser.new_page()
        
        try:
            # Configurar stealth
            await scraper.setup_stealth_page(page)
            
            url = "https://kr.op.gg/leaderboards/tier?region=kr"
            logger.info(f"📄 Navegando a: {url}")
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            
            # Capturar screenshot
            await page.screenshot(path="opgg_screenshot.png", full_page=True)
            logger.info("📸 Screenshot guardado: opgg_screenshot.png")
            
            # Guardar HTML
            html_content = await page.content()
            with open("opgg_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("📄 HTML guardado: opgg_page.html")
            
            # Intentar selectores comunes
            logger.info("\n🔎 Probando selectores...")
            
            selectors = [
                "[data-summoner-id]",
                "tr.ranked-player",
                "table tbody tr",
                ".leaderboard-row",
                ".player-row",
                ".summoner-row",
                "tr[class*='player']",
                "div[class*='leaderboard'] tr",
                "[class*='summoner']",
                "table tr"
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.success(f"✓ {selector}: {len(elements)} elementos")
                    # Mostrar primeros 3
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            text = await elem.inner_text()
                            preview = text.replace('\n', ' ')[:100]
                            logger.info(f"     [{i}] {preview}...")
                        except:
                            pass
                else:
                    logger.debug(f"✗ {selector}: 0 elementos")
            
            # Buscar texto "Challenger" o "Grandmaster" en la página
            page_text = await page.inner_text("body")
            if "Challenger" in page_text or "Grandmaster" in page_text or "Master" in page_text:
                logger.success("✓ Página contiene texto de rankings (Challenger/Grandmaster/Master)")
            else:
                logger.warning("⚠ No se encontró texto típico de rankings")
            
            # Verificar si hay JavaScript bloqueando
            has_js_block = await page.evaluate("""
                () => {
                    // Buscar indicios de detección de bot
                    return {
                        hasCloudflare: !!document.querySelector('[id*="cf"]'),
                        hasRecaptcha: !!document.querySelector('.g-recaptcha'),
                        hasAntiBot: document.body.innerText.includes('Just a moment') ||
                                   document.body.innerText.includes('Checking your browser'),
                        bodyText: document.body.innerText.substring(0, 200)
                    }
                }
            """)
            
            logger.info(f"\n🛡️ Detección de protecciones:")
            logger.info(f"   Cloudflare: {has_js_block['hasCloudflare']}")
            logger.info(f"   reCAPTCHA: {has_js_block['hasRecaptcha']}")
            logger.info(f"   Anti-bot: {has_js_block['hasAntiBot']}")
            logger.info(f"   Texto inicial: {has_js_block['bodyText']}")
            
        finally:
            await page.close()
    
    logger.success("\n✅ Análisis completado. Revisa los archivos:")
    logger.info("   - opgg_screenshot.png")
    logger.info("   - opgg_page.html")

if __name__ == "__main__":
    asyncio.run(debug_opgg())
