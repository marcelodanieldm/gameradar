"""
Pipeline principal de GameRadar AI
Orquestación del flujo completo: Scraping -> Bronze -> Silver -> Gold -> Airtable
"""
import asyncio
from typing import List
from loguru import logger

from scrapers import OPGGScraper, LiquipediaScraper, ScraperFactory
from supabase_client import SupabaseClient
from airtable_client import AirtableClient
from models import PlayerProfile


class GameRadarPipeline:
    """Pipeline completo de ingesta y procesamiento de datos"""
    
    def __init__(self):
        """Inicializa el pipeline con todos los clientes"""
        self.supabase = SupabaseClient()
        self.airtable = AirtableClient()
        logger.info("🚀 GameRadar Pipeline inicializado")
    
    async def run_scraping_to_bronze(self, source: str, identifiers: List[str]) -> int:
        """
        Paso 1: Scrapea datos y los inserta en Bronze
        
        Args:
            source: Fuente del scraping (opgg, liquipedia)
            identifiers: Lista de identificadores a scrapear
            
        Returns:
            Número de registros insertados en Bronze
        """
        logger.info(f"📥 PASO 1: Iniciando scraping desde {source}")
        
        # Crear scraper
        scraper = ScraperFactory.create_scraper(source)
        
        inserted_count = 0
        
        async with scraper:
            # Scrapear jugadores
            profiles = await scraper.scrape_players(identifiers)
            
            # Insertar cada perfil en Bronze
            for profile in profiles:
                try:
                    # Convertir perfil a diccionario para Bronze
                    raw_data = profile.model_dump(mode='json')
                    
                    # Insertar en Bronze (el trigger automáticamente lo normaliza a Silver)
                    self.supabase.insert_bronze_raw(
                        raw_data=raw_data,
                        source=source,
                        source_url=profile.profile_url
                    )
                    
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error insertando en Bronze: {e}")
        
        logger.success(f"✓ PASO 1 completado: {inserted_count} registros en Bronze")
        return inserted_count
    
    def verify_silver_data(self, country: str = None, game: str = None) -> List[dict]:
        """
        Paso 2: Verifica que los datos fueron normalizados correctamente en Silver
        
        Args:
            country: Filtro opcional por país
            game: Filtro opcional por juego
            
        Returns:
            Lista de jugadores en Silver
        """
        logger.info("🔍 PASO 2: Verificando datos en Silver")
        
        if country and game:
            players = self.supabase.get_players_by_country(country, game)
        elif country:
            players = self.supabase.get_players_by_country(country)
        else:
            # Obtener todos los jugadores recientes
            players = self.supabase.get_players_by_country("KR", limit=100)
        
        logger.success(f"✓ PASO 2 completado: {len(players)} jugadores en Silver")
        
        # Log de resumen
        for player in players[:5]:  # Mostrar primeros 5
            logger.info(
                f"  → {player['nickname']} ({player['country']}) - "
                f"Rank: {player['rank']} | WR: {player['stats'].get('win_rate', 0)}%"
            )
        
        return players
    
    def promote_best_to_gold(self, min_win_rate: float = 55.0, limit: int = 50) -> int:
        """
        Paso 3: Promociona los mejores jugadores a Gold
        
        Args:
            min_win_rate: Win rate mínimo para promoción
            limit: Número máximo de jugadores a promocionar
            
        Returns:
            Número de jugadores promocionados
        """
        logger.info(f"⭐ PASO 3: Promocionando top jugadores a Gold (WR >= {min_win_rate}%)")
        
        # Obtener jugadores de alto nivel de Silver
        # (En producción, esto debería ser una query más sofisticada)
        players = self.supabase.get_players_by_country("KR", limit=limit)
        
        promoted_count = 0
        
        for player in players:
            # Filtrar por win rate
            win_rate = player['stats'].get('win_rate', 0)
            
            if win_rate >= min_win_rate:
                try:
                    self.supabase.promote_to_gold(
                        silver_id=player['id'],
                        enrichment_notes=f"Auto-promoted: WR {win_rate}%",
                        verified_by="system"
                    )
                    promoted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error promocionando jugador {player['nickname']}: {e}")
        
        logger.success(f"✓ PASO 3 completado: {promoted_count} jugadores promocionados a Gold")
        return promoted_count
    
    def sync_to_airtable(self, country: str = None, game: str = None, limit: int = 50) -> int:
        """
        Paso 4: Sincroniza jugadores de Silver/Gold a Airtable
        
        Args:
            country: Filtro opcional por país
            game: Filtro opcional por juego
            limit: Número máximo de jugadores a sincronizar
            
        Returns:
            Número de jugadores sincronizados
        """
        logger.info(f"📤 PASO 4: Sincronizando a Airtable")
        
        # Obtener jugadores de Silver
        players = self.supabase.get_players_by_country(country or "KR", game, limit=limit)
        
        synced_count = 0
        
        # Sincronizar en batches de 10 (límite de Airtable)
        batch_size = 10
        
        for i in range(0, len(players), batch_size):
            batch = players[i:i+batch_size]
            
            # Convertir a PlayerProfile
            profiles = []
            for player_data in batch:
                try:
                    # Reconstruir PlayerProfile desde los datos de Supabase
                    profile = PlayerProfile(
                        nickname=player_data['nickname'],
                        game=player_data['game'],
                        country=player_data['country'],
                        server=player_data['server'],
                        rank=player_data['rank'] or "Unknown",
                        stats=player_data['stats'],
                        top_champions=player_data['top_champions'],
                        profile_url=player_data['profile_url']
                    )
                    profiles.append(profile)
                    
                except Exception as e:
                    logger.error(f"Error convirtiendo jugador: {e}")
            
            # Enviar batch a Airtable
            if profiles:
                try:
                    self.airtable.send_players_batch(profiles)
                    synced_count += len(profiles)
                except Exception as e:
                    logger.error(f"Error enviando batch a Airtable: {e}")
        
        logger.success(f"✓ PASO 4 completado: {synced_count} jugadores sincronizados a Airtable")
        return synced_count
    
    async def run_full_pipeline(self, source: str, identifiers: List[str], sync_to_airtable: bool = True):
        """
        Ejecuta el pipeline completo
        
        Args:
            source: Fuente del scraping
            identifiers: Identificadores a scrapear
            sync_to_airtable: Si se debe sincronizar a Airtable
        """
        logger.info("="*60)
        logger.info("🎯 INICIANDO PIPELINE COMPLETO DE GAMERADAR AI")
        logger.info("="*60)
        
        try:
            # Paso 1: Scraping -> Bronze
            bronze_count = await self.run_scraping_to_bronze(source, identifiers)
            
            # Esperar un poco para que los triggers procesen
            await asyncio.sleep(2)
            
            # Paso 2: Verificar Silver
            silver_players = self.verify_silver_data()
            
            # Paso 3: Promocionar a Gold
            gold_count = self.promote_best_to_gold(min_win_rate=55.0)
            
            # Paso 4: Sincronizar a Airtable (opcional)
            if sync_to_airtable:
                airtable_count = self.sync_to_airtable(limit=50)
            
            logger.info("="*60)
            logger.success("✅ PIPELINE COMPLETADO EXITOSAMENTE")
            logger.info(f"📊 Resumen:")
            logger.info(f"  - Bronze: {bronze_count} registros")
            logger.info(f"  - Silver: {len(silver_players)} registros")
            logger.info(f"  - Gold: {gold_count} promociones")
            if sync_to_airtable:
                logger.info(f"  - Airtable: {airtable_count} sincronizados")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Error en el pipeline: {e}")
            raise


# Ejemplo de uso
async def main():
    """Función principal de ejemplo"""
    
    # Inicializar pipeline
    pipeline = GameRadarPipeline()
    
    # Lista de jugadores coreanos de ejemplo
    korean_players = [
        "Faker",
        "Chovy", 
        "ShowMaker",
        "Canyon",
        "Keria"
    ]
    
    # Ejecutar pipeline completo
    await pipeline.run_full_pipeline(
        source="opgg",
        identifiers=korean_players,
        sync_to_airtable=True
    )


if __name__ == "__main__":
    # Configurar logging
    logger.add("gameradar_pipeline.log", rotation="10 MB")
    
    # Ejecutar
    asyncio.run(main())
