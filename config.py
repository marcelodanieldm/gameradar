"""
Configuración centralizada de GameRadar AI
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    
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
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
