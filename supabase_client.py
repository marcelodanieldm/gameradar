"""
Cliente de Supabase para GameRadar AI
Manejo de capas Bronze/Silver/Gold
"""
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger
from datetime import datetime

from models import PlayerProfile, BronzeRecord
from config import settings


class SupabaseClient:
    """Cliente para interactuar con Supabase"""
    
    def __init__(self):
        """Inicializa el cliente de Supabase"""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("✓ SupabaseClient inicializado")
    
    # =====================================================
    # CAPA BRONZE: Datos crudos
    # =====================================================
    
    def insert_bronze_raw(self, raw_data: Dict[str, Any], source: str, source_url: str = "") -> Dict[str, Any]:
        """
        Inserta datos crudos en la capa Bronze
        El trigger automáticamente los normalizará a Silver
        
        Args:
            raw_data: Datos crudos del scraping
            source: Fuente del dato (liquipedia, opgg, etc)
            source_url: URL de origen
            
        Returns:
            Registro insertado
        """
        try:
            response = self.client.table("bronze_raw_data").insert({
                "raw_data": raw_data,
                "source": source,
                "source_url": source_url
            }).execute()
            
            logger.success(f"✓ Datos insertados en Bronze (source: {source})")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"✗ Error insertando en Bronze: {e}")
            raise
    
    def get_bronze_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene registros Bronze pendientes de procesar
        
        Args:
            limit: Número máximo de registros a obtener
            
        Returns:
            Lista de registros pendientes
        """
        try:
            response = self.client.table("bronze_raw_data") \
                .select("*") \
                .eq("processing_status", "pending") \
                .limit(limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo Bronze pendientes: {e}")
            raise
    
    # =====================================================
    # CAPA SILVER: Datos normalizados
    # =====================================================
    
    def get_player_by_nickname(self, nickname: str, game: str, server: str) -> Optional[Dict[str, Any]]:
        """
        Busca un jugador en Silver por nickname, game y server
        
        Args:
            nickname: Nickname del jugador
            game: Código del juego
            server: Servidor
            
        Returns:
            Datos del jugador o None
        """
        try:
            response = self.client.table("silver_players") \
                .select("*") \
                .eq("nickname", nickname) \
                .eq("game", game) \
                .eq("server", server) \
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"✗ Error buscando jugador en Silver: {e}")
            raise
    
    def get_players_by_country(self, country: str, game: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene jugadores de un país específico
        
        Args:
            country: Código del país (ISO 2 letras)
            game: Filtro opcional por juego
            limit: Número máximo de resultados
            
        Returns:
            Lista de jugadores
        """
        try:
            query = self.client.table("silver_players") \
                .select("*") \
                .eq("country", country)
            
            if game:
                query = query.eq("game", game)
            
            response = query.order("rank_numeric", desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo jugadores por país: {e}")
            raise
    
    def search_players_by_nickname_fuzzy(self, nickname: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Búsqueda difusa de jugadores por nickname (útil para caracteres Unicode)
        
        Args:
            nickname: Nickname a buscar (puede ser parcial)
            limit: Número máximo de resultados
            
        Returns:
            Lista de jugadores que coinciden
        """
        try:
            # Usando búsqueda ILIKE para soporte Unicode
            response = self.client.table("silver_players") \
                .select("*") \
                .ilike("nickname", f"%{nickname}%") \
                .limit(limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error en búsqueda difusa: {e}")
            raise
    
    def update_player_stats(self, player_id: int, stats: Dict[str, Any], top_champions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Actualiza las estadísticas de un jugador
        
        Args:
            player_id: ID del jugador en Silver
            stats: Nuevas estadísticas
            top_champions: Nuevos top champions
            
        Returns:
            Registro actualizado
        """
        try:
            response = self.client.table("silver_players") \
                .update({
                    "stats": stats,
                    "top_champions": top_champions,
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", player_id) \
                .execute()
            
            logger.success(f"✓ Stats actualizadas para jugador ID {player_id}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"✗ Error actualizando stats: {e}")
            raise
    
    # =====================================================
    # CAPA GOLD: Datos verificados
    # =====================================================
    
    def promote_to_gold(self, silver_id: int, enrichment_notes: str = "", verified_by: str = "system") -> Dict[str, Any]:
        """
        Promociona un jugador de Silver a Gold
        
        Args:
            silver_id: ID del jugador en Silver
            enrichment_notes: Notas de enriquecimiento
            verified_by: Quién verificó el registro
            
        Returns:
            Registro Gold creado
        """
        try:
            # Obtener datos de Silver
            silver_player = self.client.table("silver_players") \
                .select("*") \
                .eq("id", silver_id) \
                .execute()
            
            if not silver_player.data:
                raise ValueError(f"Jugador Silver ID {silver_id} no encontrado")
            
            player = silver_player.data[0]
            
            # Insertar en Gold
            response = self.client.table("gold_verified_players").insert({
                "silver_id": silver_id,
                "nickname": player["nickname"],
                "game": player["game"],
                "country": player["country"],
                "server": player["server"],
                "rank": player["rank"],
                "rank_numeric": player["rank_numeric"],
                "stats": player["stats"],
                "top_champions": player["top_champions"],
                "profile_url": player["profile_url"],
                "enrichment_notes": enrichment_notes,
                "is_verified": True,
                "verified_by": verified_by,
                "verification_date": datetime.utcnow().isoformat()
            }).execute()
            
            logger.success(f"✓ Jugador '{player['nickname']}' promocionado a Gold")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"✗ Error promocionando a Gold: {e}")
            raise
    
    def get_top_players(self, country: Optional[str] = None, game: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene los top jugadores de la capa Gold
        
        Args:
            country: Filtro opcional por país
            game: Filtro opcional por juego
            limit: Número máximo de resultados
            
        Returns:
            Lista de top jugadores
        """
        try:
            query = self.client.table("gold_verified_players") \
                .select("*")
            
            if country:
                query = query.eq("country", country)
            
            if game:
                query = query.eq("game", game)
            
            response = query.order("talent_score", desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo top players: {e}")
            raise
    
    # =====================================================
    # VISTAS Y ESTADÍSTICAS
    # =====================================================
    
    def get_stats_by_region(self) -> List[Dict[str, Any]]:
        """
        Obtiene estadísticas agregadas por región
        
        Returns:
            Estadísticas por región
        """
        try:
            response = self.client.table("vw_stats_by_region") \
                .select("*") \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo stats por región: {e}")
            raise
    
    def get_top_players_by_country(self, country: str, game: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene top players de un país usando la vista
        
        Args:
            country: Código del país
            game: Código del juego
            limit: Número de resultados
            
        Returns:
            Top players del país
        """
        try:
            response = self.client.table("vw_top_players_by_country") \
                .select("*") \
                .eq("country", country) \
                .eq("game", game) \
                .lte("rank_in_country", limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo top players by country: {e}")
            raise
