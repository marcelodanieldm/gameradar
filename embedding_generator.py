"""
Generador de Embeddings Semánticos para GameRadar AI
Utiliza OpenAI text-embedding-3-small para crear vectores de 1536D

Vector semántico: Descripción natural del jugador
Ejemplo: "Jugador de región KR con 5.2 de KDA y 62% de winrate en el rango Challenger"
"""
from __future__ import annotations

import argparse
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from openai import OpenAI

from supabase_client import SupabaseClient
from config import settings


# Configuración de batches
BATCH_SIZE = 50  # Jugadores por batch
OPENAI_RATE_LIMIT_DELAY = 0.5  # Segundos entre requests para evitar rate limits


def create_player_description(player: Dict[str, Any]) -> str:
    """
    Crea una descripción en lenguaje natural del jugador para embeddings.
    
    Args:
        player: Registro de silver_players con stats
        
    Returns:
        String descriptivo del jugador
    """
    nickname = player.get("nickname", "Unknown")
    country = player.get("country", "XX")
    game = player.get("game", "Unknown")
    rank = player.get("rank", "Unranked")
    
    stats = player.get("stats", {})
    if isinstance(stats, str):
        stats = {}
    
    kda = stats.get("kda", 0.0)
    win_rate = stats.get("win_rate", 0.0)
    
    # Top champions para agregar contexto
    top_champions = player.get("top_champions", [])
    if isinstance(top_champions, list) and top_champions:
        champ_names = [c.get("name", "") for c in top_champions[:3] if isinstance(c, dict)]
        champions_str = f" especializado en {', '.join(champ_names)}" if champ_names else ""
    else:
        champions_str = ""
    
    description = (
        f"Jugador de {game} en región {country} con {kda:.2f} de KDA "
        f"y {win_rate:.1f}% de winrate en el rango {rank}{champions_str}. "
        f"Nickname: {nickname}"
    )
    
    return description


def generate_embeddings_batch(
    client: OpenAI,
    descriptions: List[str],
    model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """
    Genera embeddings para un batch de descripciones usando OpenAI.
    
    Args:
        client: Cliente de OpenAI
        descriptions: Lista de descripciones de jugadores
        model: Modelo de embeddings (default: text-embedding-3-small)
        
    Returns:
        Lista de vectores de embeddings (1536D cada uno)
    """
    try:
        response = client.embeddings.create(
            input=descriptions,
            model=model
        )
        
        embeddings = [item.embedding for item in response.data]
        logger.debug(f"✓ Generados {len(embeddings)} embeddings usando {model}")
        return embeddings
        
    except Exception as e:
        logger.error(f"✗ Error al generar embeddings: {e}")
        return []


def format_pgvector(vector: List[float]) -> str:
    """
    Formatea el vector para pgvector: "[0.1,0.2,...,0.1536]"
    
    Args:
        vector: Vector de embeddings (1536 dimensiones)
        
    Returns:
        String formateado para PostgreSQL pgvector
    """
    return "[" + ",".join(f"{v:.8f}" for v in vector) + "]"


def fetch_players_without_embeddings(
    supabase: SupabaseClient,
    limit: int,
    country: Optional[str] = None,
    game: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene jugadores de silver_players que no tienen embedding_vector en gold_analytics.
    
    Args:
        supabase: Cliente de Supabase
        limit: Número máximo de jugadores a obtener
        country: Filtro opcional por país
        game: Filtro opcional por juego
        
    Returns:
        Lista de jugadores sin embeddings
    """
    try:
        # Subquery: player_ids que YA tienen embedding_vector en gold_analytics
        gold_response = supabase.client.table("gold_analytics").select("player_id").not_.is_("embedding_vector", "null").execute()
        
        players_with_embeddings = {row["player_id"] for row in gold_response.data} if gold_response.data else set()
        
        logger.info(f"ℹ️  Encontrados {len(players_with_embeddings)} jugadores con embeddings existentes")
        
        # Query de silver_players
        query = supabase.client.table("silver_players").select(
            "id,nickname,game,country,server,rank,stats,top_champions"
        )
        
        if country:
            query = query.eq("country", country)
        if game:
            query = query.eq("game", game)
        
        response = query.limit(limit * 2).execute()  # Obtenemos más para compensar filtro
        all_players = response.data or []
        
        # Filtrar los que NO tienen embeddings
        players_without_embeddings = [
            p for p in all_players 
            if p.get("id") not in players_with_embeddings
        ][:limit]
        
        logger.info(f"✓ Encontrados {len(players_without_embeddings)} jugadores sin embeddings")
        return players_without_embeddings
        
    except Exception as e:
        logger.error(f"✗ Error al obtener jugadores: {e}")
        return []


def upsert_embedding_to_gold(
    supabase: SupabaseClient,
    player: Dict[str, Any],
    embedding: List[float],
    dry_run: bool = False
) -> bool:
    """
    Inserta o actualiza el embedding_vector en gold_analytics.
    
    Args:
        supabase: Cliente de Supabase
        player: Registro del jugador
        embedding: Vector de embedding (1536D)
        dry_run: Si es True, solo simula la operación
        
    Returns:
        True si la operación fue exitosa
    """
    player_id = player.get("id")
    nickname = player.get("nickname", "Unknown")
    
    embedding_str = format_pgvector(embedding)
    
    if dry_run:
        logger.info(f"[DRY-RUN] Actualizaría embedding para {nickname} (ID: {player_id})")
        logger.debug(f"[DRY-RUN] Vector length: {len(embedding)} dimensions")
        return True
    
    try:
        # Verificar si existe registro en gold_analytics
        existing = supabase.client.table("gold_analytics").select("id").eq("player_id", player_id).limit(1).execute()
        
        if existing.data:
            # UPDATE: Solo actualizar el embedding_vector
            gold_id = existing.data[0]["id"]
            supabase.client.table("gold_analytics").update({
                "embedding_vector": embedding_str,
                "last_updated": "now()"
            }).eq("id", gold_id).execute()
            
            logger.success(f"✓ Embedding actualizado para {nickname} (gold_id: {gold_id})")
        else:
            # INSERT: Crear nuevo registro en gold_analytics con datos mínimos
            # Nota: El trigger de silver_players normalmente crea el registro completo
            stats = player.get("stats", {})
            
            supabase.client.table("gold_analytics").insert({
                "player_id": player_id,
                "nickname": player.get("nickname", "Unknown"),
                "country_code": player.get("country", "XX"),
                "region": player.get("server", "Unknown"),
                "game": player.get("game", "Unknown"),
                "win_rate": stats.get("win_rate", 0.0) if isinstance(stats, dict) else 0.0,
                "kda": stats.get("kda", 0.0) if isinstance(stats, dict) else 0.0,
                "games_played": stats.get("games_analyzed", 0) if isinstance(stats, dict) else 0,
                "gameradar_score": 0.0,  # Será calculado por función SQL
                "embedding_vector": embedding_str
            }).execute()
            
            logger.success(f"✓ Nuevo registro en gold_analytics para {nickname}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error al guardar embedding para {nickname}: {e}")
        return False


def main(
    limit: int = 100,
    country: Optional[str] = None,
    game: Optional[str] = None,
    dry_run: bool = False,
    batch_size: int = BATCH_SIZE
):
    """
    Proceso principal de generación de embeddings.
    
    Args:
        limit: Número máximo de jugadores a procesar
        country: Filtro opcional por país (ej: KR, IN, VN)
        game: Filtro opcional por juego (ej: LOL, VAL)
        dry_run: Si es True, no guarda en la BD
        batch_size: Tamaño de batch para procesamiento
    """
    logger.info("=" * 60)
    logger.info("GameRadar AI - Generador de Embeddings Semánticos")
    logger.info("=" * 60)
    
    # Inicializar clientes
    supabase = SupabaseClient()
    
    # Verificar que existe la API key de OpenAI
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("✗ OPENAI_API_KEY no configurada en variables de entorno")
        return
    
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("✓ Cliente OpenAI inicializado")
    
    # Obtener jugadores sin embeddings
    logger.info(f"Buscando hasta {limit} jugadores sin embeddings...")
    if country:
        logger.info(f"  Filtro: country={country}")
    if game:
        logger.info(f"  Filtro: game={game}")
    
    players = fetch_players_without_embeddings(supabase, limit, country, game)
    
    if not players:
        logger.warning("⚠️  No se encontraron jugadores para procesar")
        return
    
    logger.info(f"Procesando {len(players)} jugadores en batches de {batch_size}...")
    
    # Procesar en batches
    total_success = 0
    total_errors = 0
    
    for i in range(0, len(players), batch_size):
        batch = players[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(players) + batch_size - 1) // batch_size
        
        logger.info(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} jugadores)")
        
        # Crear descripciones
        descriptions = [create_player_description(p) for p in batch]
        
        # Generar embeddings
        embeddings = generate_embeddings_batch(openai_client, descriptions)
        
        if len(embeddings) != len(batch):
            logger.error(f"✗ Mismatch en embeddings: esperados {len(batch)}, recibidos {len(embeddings)}")
            total_errors += len(batch)
            continue
        
        # Guardar embeddings
        for player, embedding in zip(batch, embeddings):
            success = upsert_embedding_to_gold(supabase, player, embedding, dry_run)
            if success:
                total_success += 1
            else:
                total_errors += 1
        
        # Rate limiting para no saturar la API de OpenAI
        if i + batch_size < len(players):
            logger.debug(f"⏳ Esperando {OPENAI_RATE_LIMIT_DELAY}s antes del siguiente batch...")
            time.sleep(OPENAI_RATE_LIMIT_DELAY)
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("Resumen de procesamiento:")
    logger.info(f"  ✓ Exitosos: {total_success}")
    logger.info(f"  ✗ Errores: {total_errors}")
    logger.info(f"  📊 Total procesados: {total_success + total_errors}")
    if dry_run:
        logger.info("  ⚠️  Modo DRY-RUN: No se guardaron datos")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera embeddings semánticos para jugadores usando OpenAI"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Número máximo de jugadores a procesar (default: 100)"
    )
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Filtrar por país (ej: KR, IN, VN, CN, JP)"
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Filtrar por juego (ej: LOL, VAL, DOTA2)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin guardar en la base de datos"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Tamaño de batch para procesamiento (default: {BATCH_SIZE})"
    )
    
    args = parser.parse_args()
    
    main(
        limit=args.limit,
        country=args.country,
        game=args.game,
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
