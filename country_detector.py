"""
Utilidades para detección de país basado en banderas y servidores
"""
from typing import Optional
import re
from models import CountryCode


# Mapeo de servidores a países
SERVER_TO_COUNTRY = {
    # League of Legends
    "kr": CountryCode.KOREA,
    "vn": CountryCode.VIETNAM,
    "ph": CountryCode.PHILIPPINES,
    "sg": CountryCode.VIETNAM,  # SEA server
    "th": CountryCode.THAILAND,
    "tw": CountryCode.TAIWAN,
    "jp": CountryCode.JAPAN,
    "in": CountryCode.INDIA,
    
    # Valorant
    "korea": CountryCode.KOREA,
    "mumbai": CountryCode.INDIA,
    "singapore": CountryCode.VIETNAM,
    "hongkong": CountryCode.CHINA,
    "tokyo": CountryCode.JAPAN,
    
    # Genéricos
    "sea": CountryCode.VIETNAM,
    "asia": CountryCode.UNKNOWN,
}


# Mapeo de códigos de bandera emoji a países
FLAG_TO_COUNTRY = {
    "🇮🇳": CountryCode.INDIA,
    "🇰🇷": CountryCode.KOREA,
    "🇻🇳": CountryCode.VIETNAM,
    "🇨🇳": CountryCode.CHINA,
    "🇵🇭": CountryCode.PHILIPPINES,
    "🇹🇭": CountryCode.THAILAND,
    "🇯🇵": CountryCode.JAPAN,
    "🇹🇼": CountryCode.TAIWAN,
    "🇮🇩": CountryCode.INDONESIA,
}


# Mapeo de nombres de país a CountryCode
COUNTRY_NAME_TO_CODE = {
    "india": CountryCode.INDIA,
    "korea": CountryCode.KOREA,
    "south korea": CountryCode.KOREA,
    "vietnam": CountryCode.VIETNAM,
    "china": CountryCode.CHINA,
    "philippines": CountryCode.PHILIPPINES,
    "thailand": CountryCode.THAILAND,
    "japan": CountryCode.JAPAN,
    "taiwan": CountryCode.TAIWAN,
    "indonesia": CountryCode.INDONESIA,
    # Nombres en idiomas locales
    "भारत": CountryCode.INDIA,
    "한국": CountryCode.KOREA,
    "việt nam": CountryCode.VIETNAM,
    "中国": CountryCode.CHINA,
}


def detect_country_from_flag(text: str) -> Optional[CountryCode]:
    """
    Detecta país a partir de banderas emoji en el texto
    
    Args:
        text: Texto que puede contener emoji de banderas
        
    Returns:
        CountryCode si se detecta, None si no
    """
    for flag, country in FLAG_TO_COUNTRY.items():
        if flag in text:
            return country
    return None


def detect_country_from_server(server: str) -> Optional[CountryCode]:
    """
    Detecta país a partir del nombre del servidor
    
    Args:
        server: Nombre del servidor (ej: "kr", "mumbai", "singapore")
        
    Returns:
        CountryCode si se detecta, None si no
    """
    server_lower = server.lower().strip()
    return SERVER_TO_COUNTRY.get(server_lower)


def detect_country_from_url(url: str) -> Optional[CountryCode]:
    """
    Detecta país a partir de la URL del perfil
    
    Args:
        url: URL del perfil
        
    Returns:
        CountryCode si se detecta, None si no
    """
    url_lower = url.lower()
    
    # Buscar códigos de país en la URL
    if "/kr/" in url_lower or "kr.op.gg" in url_lower:
        return CountryCode.KOREA
    elif "/vn/" in url_lower or "vn.op.gg" in url_lower:
        return CountryCode.VIETNAM
    elif "/in/" in url_lower or ".in/" in url_lower:
        return CountryCode.INDIA
    elif "/cn/" in url_lower or ".cn/" in url_lower:
        return CountryCode.CHINA
    elif "/jp/" in url_lower or ".jp/" in url_lower:
        return CountryCode.JAPAN
    
    return None


def detect_country_from_name(text: str) -> Optional[CountryCode]:
    """
    Detecta país a partir del nombre del país en el texto
    
    Args:
        text: Texto que puede contener el nombre del país
        
    Returns:
        CountryCode si se detecta, None si no
    """
    text_lower = text.lower().strip()
    
    for country_name, code in COUNTRY_NAME_TO_CODE.items():
        if country_name in text_lower:
            return code
    
    return None


def detect_country(
    profile_text: Optional[str] = None,
    server: Optional[str] = None,
    url: Optional[str] = None,
    additional_text: Optional[str] = None
) -> CountryCode:
    """
    Detecta el país de un jugador usando múltiples fuentes de información
    
    Prioridad:
    1. Bandera en el perfil
    2. Servidor
    3. URL
    4. Texto adicional
    5. UNKNOWN si no se detecta
    
    Args:
        profile_text: Texto del perfil del jugador
        server: Nombre del servidor
        url: URL del perfil
        additional_text: Texto adicional para analizar
        
    Returns:
        CountryCode detectado (o UNKNOWN si no se pudo determinar)
    """
    # Intentar detectar desde bandera
    if profile_text:
        country = detect_country_from_flag(profile_text)
        if country:
            return country
        
        # Intentar detectar desde nombre de país
        country = detect_country_from_name(profile_text)
        if country:
            return country
    
    # Intentar detectar desde servidor
    if server:
        country = detect_country_from_server(server)
        if country:
            return country
    
    # Intentar detectar desde URL
    if url:
        country = detect_country_from_url(url)
        if country:
            return country
    
    # Intentar detectar desde texto adicional
    if additional_text:
        country = detect_country_from_flag(additional_text)
        if country:
            return country
        
        country = detect_country_from_name(additional_text)
        if country:
            return country
    
    # Si no se detectó nada, retornar UNKNOWN
    return CountryCode.UNKNOWN


def get_server_region(country: CountryCode) -> str:
    """
    Obtiene la región del servidor basado en el país
    
    Args:
        country: Código del país
        
    Returns:
        Nombre de la región
    """
    if country in [CountryCode.KOREA, CountryCode.JAPAN]:
        return "East Asia"
    elif country in [CountryCode.CHINA, CountryCode.TAIWAN]:
        return "Greater China"
    elif country in [CountryCode.INDIA]:
        return "South Asia"
    elif country in [CountryCode.VIETNAM, CountryCode.PHILIPPINES, 
                      CountryCode.THAILAND, CountryCode.INDONESIA]:
        return "Southeast Asia"
    else:
        return "Asia Pacific"
