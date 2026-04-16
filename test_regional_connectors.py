"""
Script de prueba para Regional Connectors
Demuestra el uso de Dak.gg y ScoreGG scrapers
"""
import asyncio
from loguru import logger
from RegionalConnectors import (
    DakGGConnector,
    ScoreGGConnector,
    scrape_dak_gg_players,
    scrape_scoregg_players
)


async def test_dak_gg():
    """Prueba del conector Dak.gg (Corea)"""
    logger.info("="*80)
    logger.info("🧪 TEST: DAK.GG CONNECTOR (KOREA)")
    logger.info("="*80)
    
    # Test individual
    async with DakGGConnector() as connector:
        # Probar con un jugador
        profile = await connector.scrape_player("Faker", game="lol")
        
        if profile:
            logger.success(f"✅ Perfil scraped exitosamente:")
            logger.info(f"   - Nickname: {profile.nickname}")
            logger.info(f"   - Rank: {profile.rank}")
            logger.info(f"   - WinRate: {profile.stats.win_rate}%")
            logger.info(f"   - KDA: {profile.stats.kda}")
            logger.info(f"   - Most Played Hero: {profile.top_champions[0].name}")
            
            # Insertar en Bronze
            await connector.insert_to_bronze(profile, "dak.gg")
        else:
            logger.error("❌ No se pudo scrapear el perfil")
    
    logger.info("="*80 + "\n")


async def test_scoregg():
    """Prueba del conector ScoreGG (China)"""
    logger.info("="*80)
    logger.info("🧪 TEST: SCOREGG CONNECTOR (CHINA)")
    logger.info("="*80)
    
    # Test con proxy rotativo
    async with ScoreGGConnector(use_proxy=False) as connector:  # use_proxy=True en producción
        # Probar con un jugador
        profile = await connector.scrape_player("test_player", game="lol")
        
        if profile:
            logger.success(f"✅ Perfil scraped exitosamente:")
            logger.info(f"   - Nickname: {profile.nickname}")
            logger.info(f"   - Rank: {profile.rank}")
            logger.info(f"   - WinRate: {profile.stats.win_rate}%")
            logger.info(f"   - KDA: {profile.stats.kda}")
            logger.info(f"   - Most Played Hero: {profile.top_champions[0].name}")
            
            # Insertar en Bronze
            await connector.insert_to_bronze(profile, "scoregg.com")
        else:
            logger.warning("⚠️ No se pudo scrapear el perfil (puede ser porque el sitio requiere proxy)")
    
    logger.info("="*80 + "\n")


async def test_batch_scraping():
    """Prueba de scraping en batch"""
    logger.info("="*80)
    logger.info("🧪 TEST: BATCH SCRAPING")
    logger.info("="*80)
    
    # Batch de jugadores coreanos
    korean_players = ["Faker", "ShowMaker", "Chovy"]
    logger.info(f"📍 Scraping {len(korean_players)} jugadores de Dak.gg...")
    
    dak_profiles = await scrape_dak_gg_players(korean_players, game="lol")
    logger.success(f"✅ Scraped {len(dak_profiles)}/{len(korean_players)} jugadores de Dak.gg")
    
    logger.info("="*80 + "\n")


async def main():
    """Ejecuta todas las pruebas"""
    logger.info("\n🚀 INICIANDO PRUEBAS DE REGIONAL CONNECTORS\n")
    
    # Test 1: Dak.gg
    await test_dak_gg()
    
    # Test 2: ScoreGG
    await test_scoregg()
    
    # Test 3: Batch scraping
    await test_batch_scraping()
    
    logger.success("\n✅ TODAS LAS PRUEBAS COMPLETADAS\n")


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "test_regional_connectors_{time}.log",
        rotation="10 MB",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    asyncio.run(main())
