"""
Configuración centralizada de GameRadar AI
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Airtable
    airtable_api_key: str
    airtable_base_id: str
    airtable_table_name: str = "GameRadar_Players"
    
    # Scraper
    rate_limit_delay: int = 2
    max_concurrent_requests: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
