"""
Cliente para integración con Airtable
Envío de datos normalizados a GameRadar AI
"""
from typing import List, Dict, Any
from loguru import logger
from models import PlayerProfile, AirtableRecord
from config import settings

# Almacenamiento local para Airtable
LOCAL_AIRTABLE_STORAGE = []


class AirtableClient:
    """Cliente para enviar datos a Airtable o almacenamiento local"""
    
    def __init__(self):
        """Inicializa el cliente de Airtable (modo local o real)"""
        # Detectar si es modo local
        self.is_local = (
            settings.airtable_api_key == "local-mock-key" or
            "mock" in settings.airtable_api_key.lower() or
            "test" in settings.airtable_api_key.lower()
        )
        
        if self.is_local:
            self.api = None
            self.table = None
            logger.info(f"AirtableClient inicializado en MODO LOCAL para tabla: {settings.airtable_table_name}")
        else:
            try:
                from pyairtable import Api
                self.api = Api(settings.airtable_api_key)
                self.table = self.api.table(
                    settings.airtable_base_id, 
                    settings.airtable_table_name
                )
                logger.info(f"AirtableClient inicializado para tabla: {settings.airtable_table_name}")
            except Exception as e:
                logger.warning(f"⚠ Error conectando a Airtable, usando modo local: {e}")
                self.api = None
                self.table = None
                self.is_local = True
    
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
            
            if self.is_local:
                # Modo local - guardar en memoria
                record = {
                    "id": f"rec{len(LOCAL_AIRTABLE_STORAGE) + 1}",
                    "fields": airtable_record.model_dump(),
                    "createdTime": "2026-03-09T00:00:00.000Z"
                }
                LOCAL_AIRTABLE_STORAGE.append(record)
                logger.success(
                    f"✓ Jugador '{profile.nickname}' ({profile.country.value}) "
                    f"enviado a Airtable LOCAL - ID: {record['id']}"
                )
                return record
            else:
                # Crear registro en Airtable
                record = self.table.create(airtable_record.model_dump())
                
                logger.success(
                    f"✓ Jugador '{profile.nickname}' ({profile.country.value}) "
                    f"enviado a Airtable - ID: {record['id']}"
                )
                
                return record
            
        except Exception as e:
            logger.error(f"✗ Error enviando jugador a Airtable: {e}")
            if self.is_local:
                return {}
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
            
            if self.is_local:
                # Modo local - guardar todos en memoria
                records = []
                for record_data in airtable_records:
                    record = {
                        "id": f"rec{len(LOCAL_AIRTABLE_STORAGE) + 1}",
                        "fields": record_data,
                        "createdTime": "2026-03-09T00:00:00.000Z"
                    }
                    LOCAL_AIRTABLE_STORAGE.append(record)
                    records.append(record)
                
                logger.success(
                    f"✓ {len(records)} jugadores enviados a Airtable LOCAL en batch"
                )
                return records
            else:
                # Enviar en batch (Airtable soporta hasta 10 registros por batch)
                records = self.table.batch_create(airtable_records)
                
                logger.success(
                    f"✓ {len(records)} jugadores enviados a Airtable en batch"
                )
                
                return records
            
        except Exception as e:
            logger.error(f"✗ Error enviando batch a Airtable: {e}")
            if self.is_local:
                return []
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
            if self.is_local:
                # Modo local - buscar en memoria
                results = []
                for record in LOCAL_AIRTABLE_STORAGE:
                    fields = record.get("fields", {})
                    if fields.get("nickname") == nickname and fields.get("game") == game:
                        results.append(record)
                logger.info(f"✓ Encontrados {len(results)} registros LOCAL para '{nickname}' en {game}")
                return results
            else:
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
