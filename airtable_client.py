"""
Cliente para integración con Airtable
Envío de datos normalizados a GameRadar AI
"""
from typing import List, Dict, Any
from pyairtable import Api
from loguru import logger
from models import PlayerProfile, AirtableRecord
from config import settings


class AirtableClient:
    """Cliente para enviar datos a Airtable"""
    
    def __init__(self):
        """Inicializa el cliente de Airtable"""
        self.api = Api(settings.airtable_api_key)
        self.table = self.api.table(
            settings.airtable_base_id, 
            settings.airtable_table_name
        )
        logger.info(f"AirtableClient inicializado para tabla: {settings.airtable_table_name}")
    
    def send_player(self, profile: PlayerProfile) -> Dict[str, Any]:
        """
        Envía un perfil de jugador a Airtable
        
        Args:
            profile: PlayerProfile con datos del jugador
            
        Returns:
            Respuesta de Airtable con el registro creado
        """
        try:
            # Convertir a formato Airtable
            airtable_record = AirtableRecord.from_player_profile(profile)
            
            # Crear registro en Airtable
            record = self.table.create(airtable_record.model_dump())
            
            logger.success(
                f"✓ Jugador '{profile.nickname}' ({profile.country.value}) "
                f"enviado a Airtable - ID: {record['id']}"
            )
            
            return record
            
        except Exception as e:
            logger.error(f"✗ Error enviando jugador a Airtable: {e}")
            raise
    
    def send_players_batch(self, profiles: List[PlayerProfile]) -> List[Dict[str, Any]]:
        """
        Envía múltiples perfiles en batch a Airtable
        
        Args:
            profiles: Lista de PlayerProfile
            
        Returns:
            Lista de respuestas de Airtable
        """
        try:
            # Convertir todos los perfiles a formato Airtable
            airtable_records = [
                AirtableRecord.from_player_profile(p).model_dump() 
                for p in profiles
            ]
            
            # Enviar en batch (Airtable soporta hasta 10 registros por batch)
            records = self.table.batch_create(airtable_records)
            
            logger.success(
                f"✓ {len(records)} jugadores enviados a Airtable en batch"
            )
            
            return records
            
        except Exception as e:
            logger.error(f"✗ Error enviando batch a Airtable: {e}")
            raise
    
    def find_player_by_nickname(self, nickname: str, game: str) -> List[Dict[str, Any]]:
        """
        Busca un jugador en Airtable por nickname y juego
        
        Args:
            nickname: Nickname del jugador
            game: Código del juego
            
        Returns:
            Lista de registros encontrados
        """
        try:
            formula = f"AND({{nickname}}='{nickname}', {{game}}='{game}')"
            records = self.table.all(formula=formula)
            
            logger.info(
                f"Búsqueda en Airtable: {len(records)} registros encontrados "
                f"para '{nickname}' en {game}"
            )
            
            return records
            
        except Exception as e:
            logger.error(f"✗ Error buscando jugador en Airtable: {e}")
            raise
    
    def update_player(self, record_id: str, profile: PlayerProfile) -> Dict[str, Any]:
        """
        Actualiza un registro existente en Airtable
        
        Args:
            record_id: ID del registro en Airtable
            profile: PlayerProfile con datos actualizados
            
        Returns:
            Respuesta de Airtable con el registro actualizado
        """
        try:
            airtable_record = AirtableRecord.from_player_profile(profile)
            record = self.table.update(record_id, airtable_record.model_dump())
            
            logger.success(
                f"✓ Jugador '{profile.nickname}' actualizado en Airtable"
            )
            
            return record
            
        except Exception as e:
            logger.error(f"✗ Error actualizando jugador en Airtable: {e}")
            raise
