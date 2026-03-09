"""
Demo: Fallback Automático a Riot Games API
Demuestra cómo el sistema usa Riot API cuando el scraping falla

CONFIGURACIÓN PREVIA:
1. Obtén tu API key en: https://developer.riotgames.com/
2. Configura: $env:RIOT_API_KEY = "tu-key-aqui"
   O agrega a .env: RIOT_API_KEY=tu-key-aqui
3. Ejecuta: python demo_riot_fallback.py
"""
import asyncio
import os
from loguru import logger
from bronze_ingestion import BronzeIngestionScraper
from config import settings


async def demo_fallback():
    """Demuestra el fallback automático"""
    
    logger.info("=" * 80)
    logger.info("🎮 DEMO: Fallback Automático a Riot Games API")
    logger.info("=" * 80)
    
    # 1. Verificar configuración de API key
    api_key = settings.riot_api_key
    logger.info(f"\n📋 Verificando configuración...")
    
    if not api_key or api_key == "your-riot-api-key-here":
        logger.warning("⚠️ RIOT_API_KEY no está configurada")
        logger.info("\n📝 Para configurar:")
        logger.info("\nOpción 1: Variable de entorno (recomendado)")
        logger.info("  Windows PowerShell:")
        logger.info("    $env:RIOT_API_KEY = 'RGAPI-xxxxxxxx'")
        logger.info("\n  Linux/Mac:")
        logger.info("    export RIOT_API_KEY='RGAPI-xxxxxxxx'")
        logger.info("\nOpción 2: Archivo .env")
        logger.info("  1. Copia .env.example a .env")
        logger.info("  2. Edita .env y agrega tu RIOT_API_KEY")
        logger.info("\n🔗 Obtén tu API key gratis en:")
        logger.info("   https://developer.riotgames.com/")
        logger.info("\n💡 Sin API key, el fallback no funcionará pero el scraping sí intentará funcionar")
        
        response = input("\n¿Continuar sin API key? (s/n): ")
        if response.lower() != 's':
            return
    else:
        logger.success(f"✅ RIOT_API_KEY configurada: {api_key[:15]}...")
    
    # 2. Demo del flujo de scraping con fallback
    logger.info("\n" + "=" * 80)
    logger.info("🕷️ PASO 1: Intentar scraping de OP.GG")
    logger.info("=" * 80)
    
    async with BronzeIngestionScraper(region="KR", headless=True) as scraper:
        # El scraper automáticamente:
        # 1. Intenta scraping de OP.GG con técnicas anti-detección
        # 2. Si no obtiene jugadores, activa fallback de Riot API
        # 3. Si no hay API key, retorna lista vacía
        
        logger.info("\n🎯 Scraping OP.GG ranking (con fallback automático)...")
        players = await scraper.scrape_opgg_ranking(limit=20)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 RESULTADOS")
        logger.info("=" * 80)
        
        if len(players) > 0:
            source = players[0].get('data_source', 'unknown')
            
            if source == 'opgg':
                logger.success(f"\n✅ Scraping de OP.GG exitoso: {len(players)} jugadores")
                logger.info("💡 El fallback NO fue necesario (scraping funcionó)")
            
            elif source == 'riot_api':
                logger.success(f"\n✅ Fallback de Riot API exitoso: {len(players)} jugadores")
                logger.info("💡 OP.GG falló/bloqueó, pero Riot API funcionó perfectamente")
                logger.info("🎉 ¡Sistema de fallback automático funcionando!")
            
            # Mostrar primeros 5 jugadores
            logger.info(f"\n🏆 Top 5 jugadores ({source}):")
            for i, player in enumerate(players[:5], 1):
                name = player.get('nickname', 'Unknown')
                rank = player.get('rank', 'N/A')
                lp = player.get('lp', 'N/A')
                logger.info(f"  {i}. {name} - Rank: {rank} | LP: {lp}")
        
        else:
            logger.warning("\n⚠️ No se obtuvieron jugadores")
            
            if not api_key or api_key == "your-riot-api-key-here":
                logger.info("\n💡 Posibles causas:")
                logger.info("   1. OP.GG bloqueó el scraping (WAF)")
                logger.info("   2. Riot API fallback no disponible (API key no configurada)")
                logger.info("\n✅ Solución: Configura RIOT_API_KEY")
            else:
                logger.info("\n💡 Posibles causas:")
                logger.info("   1. OP.GG bloqueó el scraping")
                logger.info("   2. Riot API también falló (verificar API key)")
                logger.info("   3. Error de red/conectividad")


async def demo_riot_api_direct():
    """Demo de uso directo de Riot API (sin scraping)"""
    
    logger.info("\n" + "=" * 80)
    logger.info("🎮 DEMO 2: Riot API Directo (sin scraping)")
    logger.info("=" * 80)
    
    api_key = settings.riot_api_key
    
    if not api_key or api_key == "your-riot-api-key-here":
        logger.warning("\n⚠️ RIOT_API_KEY no configurada - saltando demo directo")
        return
    
    from riot_api_client import RiotAPIClient
    
    try:
        client = RiotAPIClient(api_key=api_key, region="KR")
        
        logger.info("\n🏆 Obteniendo Challenger players desde Riot API...")
        players = await client.get_top_players(limit=10)
        
        if players:
            logger.success(f"\n✅ {len(players)} jugadores obtenidos")
            logger.info("\n🏆 Top 10 Challenger (Korea):")
            
            for player in players:
                logger.info(f"  {player.rank}. {player.player_name}")
                logger.info(f"     {player.tier} | {player.lp} LP | WR: {player.win_rate}% ({player.games_played} games)")
        else:
            logger.warning("⚠️ No se obtuvieron jugadores")
    
    except Exception as e:
        logger.error(f"❌ Error usando Riot API: {e}")
        if "403" in str(e):
            logger.info("💡 API key inválida o expirada - regenera en https://developer.riotgames.com/")


async def main():
    """Ejecutar demos"""
    print("\n")
    
    # Demo 1: Scraping con fallback automático
    await demo_fallback()
    
    # Demo 2: API directo (opcional)
    response = input("\n\n¿Probar Riot API directo? (s/n): ")
    if response.lower() == 's':
        await demo_riot_api_direct()
    
    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("📚 RESUMEN")
    logger.info("=" * 80)
    logger.info("\n✅ Sistema de Fallback Automático:")
    logger.info("   1. Intenta scraping de OP.GG (NO-HEADLESS, delays largos)")
    logger.info("   2. Si falla → Usa Riot API automáticamente")
    logger.info("   3. Si no hay API key → Retorna vacío con instrucciones")
    
    logger.info("\n📖 Documentación completa:")
    logger.info("   - RIOT_API_GUIDE.md: Guía completa de configuración")
    logger.info("   - FREE_SOLUTIONS.md: Todas las soluciones gratuitas")
    
    logger.info("\n🔗 Recursos:")
    logger.info("   - API Key: https://developer.riotgames.com/")
    logger.info("   - API Docs: https://developer.riotgames.com/apis")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
