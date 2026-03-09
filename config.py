"""
Configuración centralizada de GameRadar AI
"""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Supabase (opcional - usa modo local si no está configurado)
    supabase_url: str = "http://localhost:54321"
    supabase_key: str = "local-mock-key"
    
    # Airtable (opcional)
    airtable_api_key: str = "local-mock-key"
    airtable_base_id: str = "local-mock-base"
    airtable_table_name: str = "GameRadar_Players"
    
    # Scraper
    rate_limit_delay: int = 2
    max_concurrent_requests: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    # Riot Games Official API (fallback gratuito cuando scraping falla)
    riot_api_key: str = "your-riot-api-key-here"  # Obtener en https://developer.riotgames.com/
    
    # Logging
    log_level: str = "INFO"


# Instancia global de configuración
settings = Settings()
