"""
Modelos de datos para GameRadar AI
Soporte completo para caracteres Unicode (Hindi, Chino, Coreano)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class CountryCode(str, Enum):
    """Códigos de países soportados"""
    INDIA = "IN"
    KOREA = "KR"
    VIETNAM = "VN"
    CHINA = "CN"
    PHILIPPINES = "PH"
    THAILAND = "TH"
    JAPAN = "JP"
    TAIWAN = "TW"
    INDONESIA = "ID"
    UNKNOWN = "XX"


class GameTitle(str, Enum):
    """Juegos soportados"""
    LEAGUE_OF_LEGENDS = "LOL"
    VALORANT = "VAL"
    DOTA2 = "DOTA2"
    CSGO = "CSGO"
    MOBILE_LEGENDS = "MLBB"
    PUBG_MOBILE = "PUBGM"


class Champion(BaseModel):
    """Modelo para campeón/agente"""
    name: str = Field(..., description="Nombre del campeón/agente")
    games_played: int = Field(..., ge=0, description="Partidas jugadas")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate en porcentaje")
    
    class Config:
        # Soporte Unicode completo
        json_encoders = {
            str: lambda v: v if isinstance(v, str) else str(v)
        }


class PlayerStats(BaseModel):
    """Estadísticas de un jugador (últimos 100 juegos)"""
    win_rate: float = Field(..., ge=0, le=100, description="Win rate en porcentaje")
    kda: float = Field(..., ge=0, description="KDA (Kills+Assists)/Deaths")
    kills_avg: Optional[float] = Field(None, ge=0, description="Promedio de kills")
    deaths_avg: Optional[float] = Field(None, ge=0, description="Promedio de muertes")
    assists_avg: Optional[float] = Field(None, ge=0, description="Promedio de asistencias")
    games_analyzed: int = Field(100, ge=1, le=100, description="Número de juegos analizados")


class PlayerProfile(BaseModel):
    """
    Perfil completo de jugador - Modelo principal de GameRadar AI
    Soporte completo para caracteres Unicode
    """
    # Identificación
    nickname: str = Field(..., min_length=1, max_length=100, description="Nickname del jugador")
    game: GameTitle = Field(..., description="Juego principal")
    country: CountryCode = Field(..., description="País detectado")
    server: str = Field(..., description="Servidor/Región del perfil")
    
    # Ranking
    rank: str = Field(..., description="Rango actual")
    rank_numeric: Optional[int] = Field(None, description="Conversión numérica del rango")
    
    # Estadísticas
    stats: PlayerStats = Field(..., description="Estadísticas del jugador")
    
    # Top Campeones/Agentes
    top_champions: List[Champion] = Field(
        ..., 
        min_items=1, 
        max_items=3, 
        description="Top 3 campeones/agentes"
    )
    
    # Metadatos
    profile_url: str = Field(..., description="URL del perfil original")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de scraping")
    data_quality_score: float = Field(1.0, ge=0, le=1, description="Score de calidad del dato")
    
    @validator('nickname')
    def validate_unicode_support(cls, v):
        """Valida que el nickname soporte Unicode correctamente"""
        if not v:
            raise ValueError("Nickname no puede estar vacío")
        # Asegurar que se preserve Unicode
        try:
            v.encode('utf-8').decode('utf-8')
        except UnicodeError:
            raise ValueError("Nickname contiene caracteres inválidos")
        return v
    
    @validator('top_champions')
    def validate_top_champions(cls, v):
        """Valida que haya exactamente 3 campeones o menos"""
        if len(v) > 3:
            return v[:3]  # Tomar solo los primeros 3
        return v
    
    class Config:
        # Configuración para soporte Unicode completo
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            CountryCode: lambda v: v.value,
            GameTitle: lambda v: v.value
        }
        use_enum_values = True


class BronzeRecord(BaseModel):
    """Modelo para capa Bronze (datos crudos)"""
    raw_data: dict = Field(..., description="Datos sin procesar del scraping")
    source: str = Field(..., description="Fuente del dato (Liquipedia, OP.GG, etc)")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    

class SilverRecord(BaseModel):
    """Modelo para capa Silver (datos normalizados)"""
    player_profile: PlayerProfile = Field(..., description="Perfil normalizado")
    bronze_id: Optional[int] = Field(None, description="ID del registro Bronze original")
    normalized_at: datetime = Field(default_factory=datetime.utcnow)


class GoldRecord(BaseModel):
    """Modelo para capa Gold (datos enriquecidos y validados)"""
    player_profile: PlayerProfile = Field(..., description="Perfil enriquecido")
    silver_id: Optional[int] = Field(None, description="ID del registro Silver")
    enrichment_notes: Optional[str] = Field(None, description="Notas de enriquecimiento")
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    is_verified: bool = Field(False, description="Si el perfil ha sido verificado manualmente")


class AirtableRecord(BaseModel):
    """Modelo para envío a Airtable"""
    nickname: str
    game: str
    country: str
    rank: str
    win_rate: float
    kda: float
    top_champion_1: str
    top_champion_2: Optional[str] = None
    top_champion_3: Optional[str] = None
    profile_url: str
    scraped_at: str
    
    @classmethod
    def from_player_profile(cls, profile: PlayerProfile) -> "AirtableRecord":
        """Convierte un PlayerProfile a formato Airtable"""
        return cls(
            nickname=profile.nickname,
            game=profile.game.value,
            country=profile.country.value,
            rank=profile.rank,
            win_rate=profile.stats.win_rate,
            kda=profile.stats.kda,
            top_champion_1=profile.top_champions[0].name if len(profile.top_champions) > 0 else "",
            top_champion_2=profile.top_champions[1].name if len(profile.top_champions) > 1 else None,
            top_champion_3=profile.top_champions[2].name if len(profile.top_champions) > 2 else None,
            profile_url=profile.profile_url,
            scraped_at=profile.scraped_at.isoformat()
        )
