"""Ejecuta los scrapers disponibles tras la reorganización del proyecto."""
import asyncio
from datetime import datetime
import pathlib
import sys

from loguru import logger

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ingestion.ingest_bronze_targets import main as run_ingestion_targets
from scraping.cnn_brasil_scraper import CNNBrasilNinjaScraper


async def run_bronze_ingestion() -> None:
    """Ejecuta la ingesta Bronze soportada actualmente."""
    logger.info("=" * 80)
    logger.info("📦 INICIANDO BRONZE INGESTION")
    logger.info("=" * 80)
    await run_ingestion_targets(sources=["liquipedia", "opgg_kr"], dry_run=False)
    logger.success("✅ Bronze ingestion completado exitosamente")


async def run_ninja_scraper() -> None:
    """Ejecuta el CNN Brasil Ninja Scraper."""
    logger.info("=" * 80)
    logger.info("🥷 INICIANDO CNN BRASIL NINJA SCRAPER")
    logger.info("=" * 80)
    scraper = CNNBrasilNinjaScraper(use_proxies=False)
    stats = await scraper.run_ninja_scrape()
    logger.info(f"📰 Scraped: {stats['scraped']} jugadores")
    logger.info(f"⚠️ Errores: {stats['errors']}")
    logger.info(f"⏱️ Duración: {stats['duration_seconds']}s")
    logger.success("✅ Ninja scraper completado exitosamente")


async def main() -> None:
    """Ejecuta todos los scrapers disponibles en secuencia."""
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("🚀 INICIANDO EJECUCIÓN DE SCRAPERS")
    logger.info(f"⏰ Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    await run_bronze_ingestion()
    await asyncio.sleep(2)
    await run_ninja_scraper()

    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("=" * 80)
    logger.success("🎉 SCRAPERS COMPLETADOS")
    logger.info(f"⏰ Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️  Duración total: {duration}")
    logger.info("=" * 80)


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
