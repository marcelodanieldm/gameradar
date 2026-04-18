"""Ejecuta los scrapers funcionales disponibles en la estructura nueva."""
import asyncio
from datetime import datetime
import pathlib
import sys

from loguru import logger

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ingestion.ingest_bronze_targets import main as run_ingestion_targets
from scraping.cnn_brasil_scraper import CNNBrasilNinjaScraper


async def run_bronze_ingestion():
    """Ejecuta el scraper de ingesta masiva Bronze"""
    logger.info("=" * 80)
    logger.info("📦 INICIANDO BRONZE INGESTION SCRAPER (LIQUIPEDIA)")
    logger.info("=" * 80)
    
    try:
        await run_ingestion_targets(sources=["liquipedia"], dry_run=False)
        logger.success("✅ Bronze ingestion completado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en bronze ingestion: {e}")
        raise


async def run_ninja_scraper():
    """Ejecuta el CNN Brasil Ninja Scraper"""
    logger.info("=" * 80)
    logger.info("🥷 INICIANDO CNN BRASIL NINJA SCRAPER")
    logger.info("=" * 80)
    
    try:
        scraper = CNNBrasilNinjaScraper(use_proxies=False)
        stats = await scraper.run_ninja_scrape()
        
        logger.info(f"📰 Scraped: {stats['scraped']} jugadores")
        logger.info(f"⚠️ Errores: {stats['errors']}")
        logger.info(f"⏱️ Duración: {stats['duration_seconds']}s")
        
        logger.success("✅ Ninja scraper completado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en ninja scraper: {e}")
        # No hacer raise, continuar con el siguiente scraper


async def main():
    """Ejecuta solo los scrapers que funcionan correctamente"""
    start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO SCRAPERS FUNCIONALES")
    logger.info(f"⏰ Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    scrapers_completed = []
    scrapers_failed = []
    
    # 1. Bronze ingestion (Liquipedia) - MÁS CONFIABLE
    try:
        await run_bronze_ingestion()
        scrapers_completed.append("Bronze Ingestion (Liquipedia)")
    except Exception as e:
        logger.error(f"Bronze Ingestion falló: {e}")
        scrapers_failed.append("Bronze Ingestion (Liquipedia)")
    
    await asyncio.sleep(2)  # Pausa entre scrapers
    
    # 2. CNN Brasil Ninja scraper
    try:
        await run_ninja_scraper()
        scrapers_completed.append("CNN Brasil Ninja Scraper")
    except Exception as e:
        logger.error(f"CNN Brasil Ninja Scraper falló: {e}")
        scrapers_failed.append("CNN Brasil Ninja Scraper")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("=" * 80)
    logger.success("🎉 EJECUCIÓN COMPLETADA")
    logger.info(f"⏰ Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️  Duración total: {duration}")
    logger.info("=" * 80)
    
    logger.info("\n📊 Resumen de ejecución:")
    logger.info(f"\n✅ Scrapers completados ({len(scrapers_completed)}):")
    for scraper in scrapers_completed:
        logger.info(f"  ✓ {scraper}")
    
    if scrapers_failed:
        logger.info(f"\n❌ Scrapers fallidos ({len(scrapers_failed)}):")
        for scraper in scrapers_failed:
            logger.info(f"  ✗ {scraper}")


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "working_scrapers_{time}.log",
        rotation="50 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    # Ejecutar solo scrapers funcionales
    asyncio.run(main())
