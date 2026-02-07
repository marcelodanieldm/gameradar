"""
Genera embeddings (skill_vector) desde silver_players y los guarda en gold_analytics.

Vector: [kda, winrate, agresividad, versatilidad]
- kda: normalizado 0-1
- winrate: normalizado 0-1
- agresividad: heurística basada en stats
- versatilidad: heurística basada en top_champions
"""
from __future__ import annotations

import argparse
from typing import Dict, Any, Iterable, List, Optional
from loguru import logger

from supabase_client import SupabaseClient


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _get_stat(stats: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        raw = stats.get(key, default)
        return float(raw) if raw is not None else float(default)
    except Exception:
        return float(default)


def compute_skill_vector(stats: Dict[str, Any], top_champions: List[Dict[str, Any]]) -> List[float]:
    """
    Convierte stats en un vector numérico de 4 dimensiones.
    """
    win_rate = _get_stat(stats, "win_rate", 0.0)
    kda = _get_stat(stats, "kda", 0.0)

    # Agresividad: usa campo explícito o heurística con kills/deaths
    aggressiveness = stats.get("aggressiveness")
    if aggressiveness is None:
        kills_avg = _get_stat(stats, "kills_avg", 0.0)
        deaths_avg = _get_stat(stats, "deaths_avg", 0.0)
        aggressiveness = (kills_avg / (deaths_avg + 1.0)) if kills_avg > 0 else 0.0

    # Versatilidad: usa campo explícito o diversidad de top champions
    versatility = stats.get("versatility")
    if versatility is None:
        diversity = len(top_champions) if isinstance(top_champions, list) else 0
        versatility = diversity / 3.0 if diversity > 0 else 0.0

    # Normalizaciones (0-1)
    win_rate_norm = clamp(win_rate / 100.0)
    kda_norm = clamp(kda / 10.0)  # KDA >10 se recorta
    aggressiveness_norm = clamp(float(aggressiveness) / 5.0)  # ratio ~0-5
    versatility_norm = clamp(float(versatility))  # si ya viene 0-1

    return [
        round(kda_norm, 6),
        round(win_rate_norm, 6),
        round(aggressiveness_norm, 6),
        round(versatility_norm, 6),
    ]


def format_pgvector(vector: List[float]) -> str:
    """
    Formatea el vector para pgvector: "[0.1,0.2,0.3,0.4]".
    """
    return "[" + ",".join(f"{v:.6f}" for v in vector) + "]"


def fetch_silver_players(
    supabase: SupabaseClient,
    limit: int,
    country: Optional[str],
    game: Optional[str],
) -> List[Dict[str, Any]]:
    query = supabase.client.table("silver_players").select(
        "id,nickname,game,country,server,stats,top_champions"
    )

    if country:
        query = query.eq("country", country)
    if game:
        query = query.eq("game", game)

    response = query.limit(limit).execute()
    return response.data or []


def update_skill_vector(
    supabase: SupabaseClient,
    player: Dict[str, Any],
    vector: List[float],
    dry_run: bool,
) -> bool:
    vector_payload = format_pgvector(vector)

    if dry_run:
        logger.info(
            "[DRY RUN] %s | %s | vector=%s",
            player.get("nickname"),
            player.get("game"),
            vector_payload,
        )
        return True

    # Estrategia 1: match por player_id (usar id de silver como string)
    player_id = str(player.get("id"))
    response = (
        supabase.client.table("gold_analytics")
        .update({"skill_vector": vector_payload})
        .eq("player_id", player_id)
        .execute()
    )

    if response.data:
        return True

    # Estrategia 2: fallback por nickname + game + country_code
    response = (
        supabase.client.table("gold_analytics")
        .update({"skill_vector": vector_payload})
        .eq("nickname", player.get("nickname"))
        .eq("game", player.get("game"))
        .eq("country_code", player.get("country"))
        .execute()
    )

    return bool(response.data)


def run(limit: int, country: Optional[str], game: Optional[str], dry_run: bool) -> None:
    supabase = SupabaseClient()

    players = fetch_silver_players(supabase, limit=limit, country=country, game=game)
    logger.info("Procesando %s jugadores de Silver", len(players))

    updated = 0
    skipped = 0

    for player in players:
        stats = player.get("stats") or {}
        top_champions = player.get("top_champions") or []
        vector = compute_skill_vector(stats, top_champions)

        success = update_skill_vector(supabase, player, vector, dry_run=dry_run)
        if success:
            updated += 1
        else:
            skipped += 1
            logger.warning(
                "No se pudo actualizar skill_vector para %s (%s)",
                player.get("nickname"),
                player.get("game"),
            )

    logger.success("Completado: %s actualizados, %s sin cambios", updated, skipped)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generar embeddings en gold_analytics")
    parser.add_argument("--limit", type=int, default=500, help="Máximo de jugadores a procesar")
    parser.add_argument("--country", type=str, default=None, help="Filtrar por país (ISO2)")
    parser.add_argument("--game", type=str, default=None, help="Filtrar por juego (LOL, VAL, etc)")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en Supabase")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(limit=args.limit, country=args.country, game=args.game, dry_run=args.dry_run)
