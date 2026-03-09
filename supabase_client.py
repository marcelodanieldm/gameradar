"""
Cliente de Supabase para GameRadar AI
Manejo de capas Bronze/Silver/Gold
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
import json

from models import PlayerProfile, BronzeRecord
from config import settings

# Almacenamiento local en memoria con datos de prueba
LOCAL_STORAGE = {
    "bronze_raw_data": [],
    "silver_players": [
        {
            "id": 1,
            "nickname": "Faker",
            "game": "lol",
            "country": "KR",
            "server": "kr",
            "rank": "Challenger",
            "rank_numeric": 1000,
            "stats": {"wins": 100, "losses": 50},
            "top_champions": [{"name": "Zed", "games": 50}],
            "profile_url": "https://kr.op.gg/faker",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00"
        },
        {
            "id": 2,
            "nickname": "Uzi",
            "game": "lol",
            "country": "CN",
            "server": "cn",
            "rank": "Challenger",
            "rank_numeric": 950,
            "stats": {"wins": 95, "losses": 55},
            "top_champions": [{"name": "Vayne", "games": 60}],
            "profile_url": "https://lol.qq.com/uzi",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00"
        }
    ],
    "gold_verified_players": [
        {
            "id": 1,
            "silver_id": 1,
            "nickname": "Faker",
            "game": "lol",
            "country": "KR",
            "server": "kr",
            "rank": "Challenger",
            "rank_numeric": 1000,
            "stats": {"wins": 100, "losses": 50},
            "top_champions": [{"name": "Zed", "games": 50}],
            "profile_url": "https://kr.op.gg/faker",
            "talent_score": 95.5,
            "is_verified": True,
            "verified_by": "system",
            "verification_date": "2026-01-01T00:00:00"
        }
    ]
}

class SupabaseClient:
    """Cliente para interactuar con Supabase o almacenamiento local"""
    
    def __init__(self):
        """Inicializa el cliente (modo local o Supabase)"""
        # Detectar si es modo local
        self.is_local = (
            settings.supabase_url == "http://localhost:54321" or
            settings.supabase_key == "local-mock-key" or
            "test" in settings.supabase_url.lower()
        )
        
        if self.is_local:
            self.client = None
            logger.info("✓ SupabaseClient inicializado en MODO LOCAL (sin conexión externa)")
        else:
            try:
                from supabase import create_client
                self.client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
                logger.info("✓ SupabaseClient inicializado con Supabase real")
            except Exception as e:
                logger.warning(f"⚠ Error conectando a Supabase, usando modo local: {e}")
                self.client = None
                self.is_local = True
    
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
            if self.is_local:
                # Modo local - almacenar en memoria
                record = {
                    "id": len(LOCAL_STORAGE["bronze_raw_data"]) + 1,
                    "raw_data": raw_data,
                    "source": source,
                    "source_url": source_url,
                    "created_at": datetime.now().isoformat(),
                    "processing_status": "pending"
                }
                LOCAL_STORAGE["bronze_raw_data"].append(record)
                logger.success(f"✓ Datos insertados en Bronze LOCAL (source: {source})")
                return record
            else:
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
            if self.is_local:
                # Modo local - filtrar en memoria
                pending = [r for r in LOCAL_STORAGE["bronze_raw_data"] 
                          if r.get("processing_status") == "pending"]
                return pending[:limit]
            else:
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
            if self.is_local:
                # Modo local - buscar en memoria
                for player in LOCAL_STORAGE["silver_players"]:
                    if (player.get("nickname") == nickname and 
                        player.get("game") == game and 
                        player.get("server") == server):
                        return player
                return None
            else:
                response = self.client.table("silver_players") \
                    .select("*") \
                    .eq("nickname", nickname) \
                    .eq("game", game) \
                    .eq("server", server) \
                .execute()
            
            if self.is_local:
                return None
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"✗ Error buscando jugador en Silver: {e}")
            if self.is_local:
                return None
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
            if self.is_local:
                # Modo local - filtrar en memoria
                players = [p for p in LOCAL_STORAGE["silver_players"]
                          if p.get("country") == country]
                if game:
                    players = [p for p in players if p.get("game") == game]
                # Ordenar por rank_numeric descendente
                players.sort(key=lambda x: x.get("rank_numeric", 0), reverse=True)
                return players[:limit]
            else:
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
            if self.is_local:
                return []
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
            if self.is_local:
                # Modo local - búsqueda simple en memoria
                nickname_lower = nickname.lower()
                results = [p for p in LOCAL_STORAGE["silver_players"]
                          if nickname_lower in p.get("nickname", "").lower()]
                return results[:limit]
            else:
                # Usando búsqueda ILIKE para soporte Unicode
                response = self.client.table("silver_players") \
                    .select("*") \
                    .ilike("nickname", f"%{nickname}%") \
                    .limit(limit) \
                    .execute()
                
                return response.data
            
        except Exception as e:
            logger.error(f"✗ Error en búsqueda difusa: {e}")
            if self.is_local:
                return []
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
            if self.is_local:
                # Modo local - actualizar en memoria
                for player in LOCAL_STORAGE["silver_players"]:
                    if player.get("id") == player_id:
                        player["stats"] = stats
                        player["top_champions"] = top_champions
                        player["updated_at"] = datetime.now().isoformat()
                        logger.success(f"✓ Stats actualizadas para jugador ID {player_id} (LOCAL)")
                        return player
                return {}
            else:
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
            if self.is_local:
                return {}
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
            if self.is_local:
                # Modo local - buscar en Silver y crear en Gold
                player = None
                for p in LOCAL_STORAGE["silver_players"]:
                    if p.get("id") == silver_id:
                        player = p.copy()
                        break
                
                if not player:
                    raise ValueError(f"Jugador Silver ID {silver_id} no encontrado")
                
                gold_record = {
                    "id": len(LOCAL_STORAGE["gold_verified_players"]) + 1,
                    "silver_id": silver_id,
                    "nickname": player["nickname"],
                    "game": player["game"],
                    "country": player.get("country"),
                    "server": player.get("server"),
                    "rank": player.get("rank"),
                    "rank_numeric": player.get("rank_numeric"),
                    "stats": player.get("stats"),
                    "top_champions": player.get("top_champions"),
                    "profile_url": player.get("profile_url"),
                    "enrichment_notes": enrichment_notes,
                    "is_verified": True,
                    "verified_by": verified_by,
                    "verification_date": datetime.now().isoformat()
                }
                LOCAL_STORAGE["gold_verified_players"].append(gold_record)
                logger.success(f"✓ Jugador '{player['nickname']}' promocionado a Gold (LOCAL)")
                return gold_record
            else:
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
            if self.is_local:
                return {}
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
            if self.is_local:
                # Modo local - filtrar en memoria
                players = LOCAL_STORAGE["gold_verified_players"].copy()
                if country:
                    players = [p for p in players if p.get("country") == country]
                if game:
                    players = [p for p in players if p.get("game") == game]
                # Ordenar por talent_score descendente
                players.sort(key=lambda x: x.get("talent_score", 0), reverse=True)
                return players[:limit]
            else:
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
            if self.is_local:
                return []
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
            if self.is_local:
                # Modo local - calcular stats básicas
                stats = {}
                for player in LOCAL_STORAGE["silver_players"]:
                    country = player.get("country", "UNKNOWN")
                    if country not in stats:
                        stats[country] = {"country": country, "player_count": 0}
                    stats[country]["player_count"] += 1
                return list(stats.values())
            else:
                response = self.client.table("vw_stats_by_region") \
                    .select("*") \
                    .execute()
                
                return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo stats por región: {e}")
            if self.is_local:
                return []
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
            if self.is_local:
                # Modo local - filtrar y rankear
                players = [p for p in LOCAL_STORAGE["silver_players"]
                          if p.get("country") == country and p.get("game") == game]
                players.sort(key=lambda x: x.get("rank_numeric", 0), reverse=True)
                return players[:limit]
            else:
                response = self.client.table("vw_top_players_by_country") \
                    .select("*") \
                    .eq("country", country) \
                    .eq("game", game) \
                    .lte("rank_in_country", limit) \
                    .execute()
                
                return response.data
            
        except Exception as e:
            logger.error(f"✗ Error obteniendo top players by country: {e}")
            if self.is_local:
                return []
            raise
