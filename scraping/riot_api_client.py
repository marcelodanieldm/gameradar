"""
Riot Games Official API Client
Fallback GRATUITO cuando el scraping de OP.GG falla

API Documentation: https://developer.riotgames.com/
Rate Limits: 20 requests/second, 100 requests/2 minutes (gratis)
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from loguru import logger
from datetime import datetime, timezone
from core.models import PlayerProfile


class RiotAPIClient:
    """Cliente para la API oficial de Riot Games"""
    
    # Endpoints por región
    REGION_ENDPOINTS = {
        "KR": "https://kr.api.riotgames.com",
        "NA": "https://na1.api.riotgames.com",
        "EUW": "https://euw1.api.riotgames.com",
        "EUNE": "https://eun1.api.riotgames.com",
        "BR": "https://br1.api.riotgames.com",
        "LAN": "https://la1.api.riotgames.com",
        "LAS": "https://la2.api.riotgames.com",
        "OCE": "https://oc1.api.riotgames.com",
        "TR": "https://tr1.api.riotgames.com",
        "RU": "https://ru.api.riotgames.com",
        "JP": "https://jp1.api.riotgames.com",
        "PH": "https://ph2.api.riotgames.com",
        "SG": "https://sg2.api.riotgames.com",
        "TH": "https://th2.api.riotgames.com",
        "TW": "https://tw2.api.riotgames.com",
        "VN": "https://vn2.api.riotgames.com",
    }
    
    # Ranking endpoints por plataforma
    PLATFORM_ROUTING = {
        "KR": "asia",
        "JP": "asia",
        "NA": "americas",
        "BR": "americas",
        "LAN": "americas",
        "LAS": "americas",
        "EUW": "europe",
        "EUNE": "europe",
        "TR": "europe",
        "RU": "europe",
        "OCE": "sea",
        "PH": "sea",
        "SG": "sea",
        "TH": "sea",
        "TW": "sea",
        "VN": "sea",
    }
    
    def __init__(self, api_key: str, region: str = "KR"):
        """
        Inicializa el cliente de Riot API
        
        Args:
            api_key: API key de Riot Games (obtener en https://developer.riotgames.com/)
            region: Región del servidor (KR, NA, EUW, etc.)
        """
        self.api_key = api_key
        self.region = region.upper()
        self.base_url = self.REGION_ENDPOINTS.get(self.region)
        
        if not self.base_url:
            raise ValueError(f"Región no soportada: {self.region}")
        
        self.headers = {
            "X-Riot-Token": self.api_key,
            "Accept": "application/json"
        }
        
        logger.info(f"🎮 RiotAPIClient inicializado para región: {self.region}")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Hace una petición HTTP a la API de Riot
        
        Args:
            endpoint: Endpoint de la API (ej: "/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5")
            params: Parámetros query opcionales
            
        Returns:
            Respuesta JSON o None si hay error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 429:
                        # Rate limit exceeded
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"⚠️ Rate limit alcanzado. Reintentando en {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(endpoint, params)
                    
                    elif response.status == 403:
                        logger.error("❌ API key inválida o expirada")
                        return None
                    
                    elif response.status == 404:
                        logger.warning(f"⚠️ Endpoint no encontrado: {endpoint}")
                        return None
                    
                    else:
                        logger.error(f"❌ Error {response.status}: {await response.text()}")
                        return None
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout en request a {url}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Error en request a Riot API: {e}")
            return None
    
    async def get_challenger_players(self, queue: str = "RANKED_SOLO_5x5") -> List[PlayerProfile]:
        """
        Obtiene los jugadores de Challenger (equivalente a top leaderboard)
        
        Args:
            queue: Tipo de cola (RANKED_SOLO_5x5, RANKED_FLEX_SR, etc.)
            
        Returns:
            Lista de PlayerProfile con los jugadores Challenger
        """
        logger.info(f"🏆 Obteniendo Challenger players para {self.region} ({queue})...")
        
        # 1. Obtener la liga Challenger
        endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"
        challenger_data = await self._make_request(endpoint)
        
        if not challenger_data:
            logger.warning("⚠️ No se pudo obtener datos de Challenger")
            return []
        
        entries = challenger_data.get("entries", [])
        logger.info(f"📊 {len(entries)} jugadores Challenger encontrados")
        
        # 2. Convertir a PlayerProfile
        players = []
        for idx, entry in enumerate(entries[:100], 1):  # Limitar a top 100
            try:
                # Datos básicos de la API
                summoner_name = entry.get("summonerName", "Unknown")
                league_points = entry.get("leaguePoints", 0)
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                total_games = wins + losses
                win_rate = round((wins / total_games * 100), 1) if total_games > 0 else 0.0
                
                player = PlayerProfile(
                    player_name=summoner_name,
                    rank=idx,
                    tier="Challenger",
                    lp=league_points,
                    win_rate=win_rate,
                    games_played=total_games,
                    region=self.region,
                    game_title="League of Legends",
                    source_url=f"https://developer.riotgames.com/apis#league-v4",
                    scraped_at=datetime.now(timezone.utc)
                )
                
                players.append(player)
            
            except Exception as e:
                logger.warning(f"⚠️ Error procesando jugador {idx}: {e}")
                continue
        
        logger.success(f"✅ {len(players)} jugadores procesados desde Riot API")
        return players
    
    async def get_grandmaster_players(self, queue: str = "RANKED_SOLO_5x5") -> List[PlayerProfile]:
        """
        Obtiene los jugadores de Grandmaster
        
        Args:
            queue: Tipo de cola
            
        Returns:
            Lista de PlayerProfile
        """
        logger.info(f"💎 Obteniendo Grandmaster players para {self.region}...")
        
        endpoint = f"/lol/league/v4/grandmasterleagues/by-queue/{queue}"
        gm_data = await self._make_request(endpoint)
        
        if not gm_data:
            return []
        
        entries = gm_data.get("entries", [])
        logger.info(f"📊 {len(entries)} jugadores Grandmaster encontrados")
        
        players = []
        for idx, entry in enumerate(entries[:100], 101):  # Rank 101-200
            try:
                player = PlayerProfile(
                    player_name=entry.get("summonerName", "Unknown"),
                    rank=idx,
                    tier="Grandmaster",
                    lp=entry.get("leaguePoints", 0),
                    win_rate=round((entry.get("wins", 0) / (entry.get("wins", 0) + entry.get("losses", 1)) * 100), 1),
                    games_played=entry.get("wins", 0) + entry.get("losses", 0),
                    region=self.region,
                    game_title="League of Legends",
                    source_url="https://developer.riotgames.com/apis#league-v4",
                    scraped_at=datetime.now(timezone.utc)
                )
                players.append(player)
            except:
                continue
        
        return players
    
    async def get_top_players(self, limit: int = 100) -> List[PlayerProfile]:
        """
        Obtiene los mejores jugadores (Challenger + Grandmaster si es necesario)
        
        Args:
            limit: Número máximo de jugadores a obtener
            
        Returns:
            Lista ordenada de PlayerProfile
        """
        logger.info(f"🎯 Obteniendo top {limit} jugadores desde Riot API...")
        
        # Obtener Challenger primero
        challenger_players = await self.get_challenger_players()
        
        if len(challenger_players) >= limit:
            return challenger_players[:limit]
        
        # Si necesitamos más jugadores, agregar Grandmaster
        if len(challenger_players) < limit:
            logger.info("📈 Agregando jugadores Grandmaster...")
            gm_players = await self.get_grandmaster_players()
            all_players = challenger_players + gm_players
            return all_players[:limit]
        
        return challenger_players


# Función helper para usar como fallback
async def fetch_players_from_riot_api(region: str, api_key: str, limit: int = 100) -> List[PlayerProfile]:
    """
    Función helper para obtener jugadores desde Riot API
    
    Args:
        region: Región del servidor (KR, NA, EUW, etc.)
        api_key: API key de Riot Games
        limit: Número de jugadores a obtener
        
    Returns:
        Lista de PlayerProfile
    """
    if not api_key or api_key == "your-riot-api-key-here":
        logger.warning("⚠️ RIOT_API_KEY no configurada - no se puede usar fallback")
        logger.info("💡 Obtén tu API key gratis en: https://developer.riotgames.com/")
        return []
    
    try:
        client = RiotAPIClient(api_key=api_key, region=region)
        players = await client.get_top_players(limit=limit)
        return players
    
    except Exception as e:
        logger.error(f"❌ Error usando Riot API como fallback: {e}")
        return []


# Demo de uso
async def main():
    """Demo de uso del cliente"""
    import os
    
    # Leer API key de variable de entorno
    api_key = os.getenv("RIOT_API_KEY", "RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    
    if api_key == "RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx":
        print("\n❌ Necesitas configurar RIOT_API_KEY")
        print("📝 Obtén tu API key gratis en: https://developer.riotgames.com/")
        print("\nLinux/Mac:")
        print("  export RIOT_API_KEY='tu-api-key-aqui'")
        print("\nWindows:")
        print("  $env:RIOT_API_KEY='tu-api-key-aqui'")
        print("\nO crea un archivo .env con:")
        print("  RIOT_API_KEY=tu-api-key-aqui")
        return
    
    # Probar cliente
    client = RiotAPIClient(api_key=api_key, region="KR")
    
    # Obtener top 10 jugadores
    players = await client.get_top_players(limit=10)
    
    print(f"\n✅ {len(players)} jugadores obtenidos:\n")
    for player in players[:5]:
        print(f"  {player.rank}. {player.player_name} - {player.tier} {player.lp}LP")
        print(f"     Win Rate: {player.win_rate}% | Games: {player.games_played}")


if __name__ == "__main__":
    asyncio.run(main())
