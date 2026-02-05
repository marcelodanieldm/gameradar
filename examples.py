"""
Ejemplos de uso de GameRadar AI
Diferentes casos de uso y flujos
"""
import asyncio
from loguru import logger

# Configurar logging
logger.add("examples.log", rotation="1 MB")


# ============================================
# Ejemplo 1: Scraping básico de OP.GG
# ============================================

async def example_opgg_scraping():
    """Ejemplo básico de scraping de OP.GG Korea"""
    from scrapers import OPGGScraper
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 1: Scraping básico de OP.GG Korea")
    logger.info("=" * 60)
    
    async with OPGGScraper() as scraper:
        # Lista de jugadores profesionales coreanos
        players = ["Faker", "Chovy", "ShowMaker"]
        
        profiles = await scraper.scrape_players(players)
        
        for profile in profiles:
            logger.info(
                f"🎮 {profile.nickname} ({profile.country.value})\n"
                f"   Rank: {profile.rank}\n"
                f"   Win Rate: {profile.stats.win_rate}%\n"
                f"   KDA: {profile.stats.kda}\n"
                f"   Top Champion: {profile.top_champions[0].name if profile.top_champions else 'N/A'}"
            )


# ============================================
# Ejemplo 2: Pipeline completo
# ============================================

async def example_full_pipeline():
    """Ejemplo de pipeline completo: Scraping -> Database -> Airtable"""
    from pipeline import GameRadarPipeline
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 2: Pipeline completo")
    logger.info("=" * 60)
    
    pipeline = GameRadarPipeline()
    
    # Jugadores de diferentes regiones
    players = [
        "Faker",      # Korea
        "Chovy",      # Korea
        "Canyon",     # Korea
    ]
    
    await pipeline.run_full_pipeline(
        source="opgg",
        identifiers=players,
        sync_to_airtable=True
    )


# ============================================
# Ejemplo 3: Consultas a Supabase
# ============================================

def example_supabase_queries():
    """Ejemplos de consultas a Supabase"""
    from supabase_client import SupabaseClient
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 3: Consultas a Supabase")
    logger.info("=" * 60)
    
    db = SupabaseClient()
    
    # 3.1: Top jugadores de Corea
    logger.info("\n3.1: Top jugadores de Corea (LOL)")
    korean_players = db.get_players_by_country("KR", game="LOL", limit=5)
    for player in korean_players:
        logger.info(f"  → {player['nickname']}: Rank {player['rank']}")
    
    # 3.2: Búsqueda difusa por nickname
    logger.info("\n3.2: Búsqueda difusa de 'Faker'")
    results = db.search_players_by_nickname_fuzzy("Faker", limit=3)
    for player in results:
        logger.info(f"  → {player['nickname']} ({player['server']})")
    
    # 3.3: Estadísticas por región
    logger.info("\n3.3: Estadísticas por región")
    stats = db.get_stats_by_region()
    for stat in stats[:5]:
        logger.info(
            f"  → {stat['country']} ({stat['game']}): "
            f"{stat['total_players']} jugadores, "
            f"avg WR: {stat['avg_win_rate']:.1f}%"
        )


# ============================================
# Ejemplo 4: Detección de país
# ============================================

def example_country_detection():
    """Ejemplo de detección de país desde diferentes fuentes"""
    from country_detector import detect_country, CountryCode
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 4: Detección de país")
    logger.info("=" * 60)
    
    # 4.1: Desde bandera emoji
    logger.info("\n4.1: Detección desde bandera emoji")
    country = detect_country(profile_text="Pro player 🇰🇷 Faker")
    logger.info(f"  → Detectado: {country.value} (Korea)")
    
    # 4.2: Desde servidor
    logger.info("\n4.2: Detección desde servidor")
    country = detect_country(server="mumbai")
    logger.info(f"  → Detectado: {country.value} (India)")
    
    # 4.3: Desde URL
    logger.info("\n4.3: Detección desde URL")
    country = detect_country(url="https://vn.op.gg/summoners/vn/player123")
    logger.info(f"  → Detectado: {country.value} (Vietnam)")
    
    # 4.4: Desde nombre de país en texto
    logger.info("\n4.4: Detección desde texto")
    country = detect_country(profile_text="Player from भारत (India)")
    logger.info(f"  → Detectado: {country.value} (India)")


# ============================================
# Ejemplo 5: Creación manual de perfiles
# ============================================

def example_manual_profile_creation():
    """Ejemplo de creación manual de perfiles con validación"""
    from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode
    from airtable_client import AirtableClient
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 5: Creación manual de perfiles")
    logger.info("=" * 60)
    
    # Crear perfil con soporte Unicode
    profile = PlayerProfile(
        nickname="भारत_गेमर",  # Nombre en Hindi
        game=GameTitle.LEAGUE_OF_LEGENDS,
        country=CountryCode.INDIA,
        server="IN",
        rank="Diamond II",
        stats=PlayerStats(
            win_rate=58.5,
            kda=3.2,
            kills_avg=7.5,
            deaths_avg=4.2,
            assists_avg=9.8,
            games_analyzed=100
        ),
        top_champions=[
            Champion(name="Yasuo", games_played=50, win_rate=60.0),
            Champion(name="Zed", games_played=30, win_rate=57.0),
            Champion(name="Lee Sin", games_played=20, win_rate=55.0)
        ],
        profile_url="https://example.com/player"
    )
    
    logger.info(f"✓ Perfil creado: {profile.nickname}")
    logger.info(f"  País: {profile.country.value}")
    logger.info(f"  Win Rate: {profile.stats.win_rate}%")
    logger.info(f"  KDA: {profile.stats.kda}")
    
    # Enviar a Airtable
    try:
        airtable = AirtableClient()
        record = airtable.send_player(profile)
        logger.success(f"✓ Enviado a Airtable: {record['id']}")
    except Exception as e:
        logger.warning(f"⚠ No se pudo enviar a Airtable (configurar .env): {e}")


# ============================================
# Ejemplo 6: Promoción a Gold y cálculo de Talent Score
# ============================================

def example_gold_promotion():
    """Ejemplo de promoción de jugadores a Gold"""
    from supabase_client import SupabaseClient
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 6: Promoción a Gold")
    logger.info("=" * 60)
    
    db = SupabaseClient()
    
    # Obtener top jugadores de Silver
    silver_players = db.get_players_by_country("KR", game="LOL", limit=10)
    
    logger.info(f"Encontrados {len(silver_players)} jugadores en Silver")
    
    # Promocionar jugadores con WR > 55%
    for player in silver_players:
        win_rate = player['stats'].get('win_rate', 0)
        
        if win_rate >= 55.0:
            try:
                gold_record = db.promote_to_gold(
                    silver_id=player['id'],
                    enrichment_notes=f"High performer: {win_rate}% WR",
                    verified_by="system"
                )
                
                logger.success(
                    f"✓ {player['nickname']} promocionado a Gold "
                    f"(WR: {win_rate}%)"
                )
            except Exception as e:
                logger.error(f"✗ Error promocionando {player['nickname']}: {e}")


# ============================================
# Ejemplo 7: Batch scraping con rate limiting
# ============================================

async def example_batch_scraping():
    """Ejemplo de scraping masivo con rate limiting"""
    from scrapers import OPGGScraper
    
    logger.info("=" * 60)
    logger.info("EJEMPLO 7: Batch scraping con rate limiting")
    logger.info("=" * 60)
    
    # Lista grande de jugadores
    players = [
        "Faker", "Chovy", "ShowMaker", "Canyon", "Keria",
        "Doran", "Oner", "Zeus", "Gumayusi", "Delight"
    ]
    
    async with OPGGScraper() as scraper:
        logger.info(f"Iniciando scraping de {len(players)} jugadores...")
        
        profiles = await scraper.scrape_players(players)
        
        logger.success(f"✓ Scraped {len(profiles)}/{len(players)} jugadores")
        
        # Calcular estadísticas
        if profiles:
            avg_wr = sum(p.stats.win_rate for p in profiles) / len(profiles)
            avg_kda = sum(p.stats.kda for p in profiles) / len(profiles)
            
            logger.info(f"📊 Estadísticas del batch:")
            logger.info(f"  - Average Win Rate: {avg_wr:.1f}%")
            logger.info(f"  - Average KDA: {avg_kda:.2f}")


# ============================================
# Función principal
# ============================================

async def run_all_examples():
    """Ejecuta todos los ejemplos"""
    
    logger.info("🚀 INICIANDO EJEMPLOS DE GAMERADAR AI\n")
    
    # Ejemplo 1: Scraping básico
    try:
        await example_opgg_scraping()
    except Exception as e:
        logger.error(f"Error en Ejemplo 1: {e}")
    
    await asyncio.sleep(2)
    
    # Ejemplo 4: Detección de país (síncrono)
    try:
        example_country_detection()
    except Exception as e:
        logger.error(f"Error en Ejemplo 4: {e}")
    
    await asyncio.sleep(1)
    
    # Ejemplo 5: Creación manual de perfiles
    try:
        example_manual_profile_creation()
    except Exception as e:
        logger.error(f"Error en Ejemplo 5: {e}")
    
    # Nota: Los ejemplos que requieren Supabase configurado están comentados
    # Para ejecutarlos, descomentar y configurar .env correctamente
    
    # Ejemplo 2: Pipeline completo
    # await example_full_pipeline()
    
    # Ejemplo 3: Consultas Supabase
    # example_supabase_queries()
    
    # Ejemplo 6: Promoción a Gold
    # example_gold_promotion()
    
    # Ejemplo 7: Batch scraping
    # await example_batch_scraping()
    
    logger.info("\n✅ EJEMPLOS COMPLETADOS")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
