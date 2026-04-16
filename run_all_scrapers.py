"""
Script para ejecutar todos los servicios de scraping de GameRadar AI
Incluye: Pipeline completo, Bronze Ingestion, y CNN Brasil Ninja Scraper
"""
import asyncio
from loguru import logger
from datetime import datetime

# Imports de todos los scrapers
from pipeline import GameRadarPipeline
from bronze_ingestion import BronzeIngestionScraper
from cnn_brasil_scraper import CNNBrasilNinjaScraper


async def run_pipeline_scraper():
    """Ejecuta el pipeline completo (OP.GG + Liquipedia)"""
    logger.info("=" * 80)
    logger.info("🎯 INICIANDO PIPELINE SCRAPER (OP.GG + Liquipedia)")
    logger.info("=" * 80)
    
    try:
        pipeline = GameRadarPipeline()
        
        # Lista de jugadores coreanos de ejemplo
        korean_players = [
            "Faker",
            "Chovy",
            "ShowMaker",
            "Canyon",
            "Keria",
            "Zeus",
            "Oner",
            "Gumayusi",
            "Doran",
            "Peyz"
        ]
        
        await pipeline.run_full_pipeline(
            source="opgg",
            identifiers=korean_players,
            sync_to_airtable=False  # Cambiar a True si quieres sync con Airtable
        )
        
        logger.success("✅ Pipeline scraper completado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en pipeline scraper: {e}")


async def run_bronze_ingestion():
    """Ejecuta el scraper de ingesta masiva Bronze"""
    logger.info("=" * 80)
    logger.info("📦 INICIANDO BRONZE INGESTION SCRAPER")
    logger.info("=" * 80)
    
    try:
        async with BronzeIngestionScraper(region="KR", headless=True) as scraper:
            # Scrapear de Liquipedia
            await scraper.run_ingestion(
                source="liquipedia",
                game="leagueoflegends",
                limit=30
            )
            
            logger.success("✅ Bronze ingestion completado exitosamente")
            
    except Exception as e:
        logger.error(f"❌ Error en bronze ingestion: {e}")


async def run_ninja_scraper():
    """Ejecuta el CNN Brasil Ninja Scraper"""
    logger.info("=" * 80)
    logger.info("🥷 INICIANDO CNN BRASIL NINJA SCRAPER")
    logger.info("=" * 80)
    
    try:
        # CNNBrasilNinjaScraper no usa context manager, tiene su propio método
        scraper = CNNBrasilNinjaScraper(use_proxies=False)
        stats = await scraper.run_ninja_scrape()
        
        logger.info(f"📰 Scraped: {stats['scraped']} jugadores")
        logger.info(f"⚠️ Errores: {stats['errors']}")
        logger.info(f"⏱️ Duración: {stats['duration_seconds']}s")
        
        logger.success("✅ Ninja scraper completado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en ninja scraper: {e}")


async def main():
    """Ejecuta todos los scrapers en secuencia"""
    start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO EJECUCIÓN DE TODOS LOS SCRAPERS")
    logger.info(f"⏰ Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # 1. Pipeline scraper (OP.GG)
    await run_pipeline_scraper()
    await asyncio.sleep(2)  # Pausa entre scrapers
    
    # 2. Bronze ingestion (Liquipedia)
    await run_bronze_ingestion()
    await asyncio.sleep(2)  # Pausa entre scrapers
    
    # 3. CNN Brasil Ninja scraper
    await run_ninja_scraper()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("=" * 80)
    logger.success("🎉 TODOS LOS SCRAPERS COMPLETADOS")
    logger.info(f"⏰ Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️  Duración total: {duration}")
    logger.info("=" * 80)
    
    logger.info("\n📊 Resumen de ejecución:")
    logger.info("  ✅ Pipeline Scraper (OP.GG + Liquipedia)")
    logger.info("  ✅ Bronze Ingestion Scraper")
    logger.info("  ✅ CNN Brasil Ninja Scraper")


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "all_scrapers_{time}.log",
        rotation="50 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    # Ejecutar todos los scrapers
    asyncio.run(main())
