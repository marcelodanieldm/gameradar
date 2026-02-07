// ============================================================================
// SUPABASE EDGE FUNCTION: Player Recommendation System
// ============================================================================
// 
// PURPOSE: Find similar amateur players to professional players using vector similarity
// OPTIMIZATION: Low-latency, data-scientist approach with pgvector cosine similarity
//
// USAGE:
//   POST https://[project].supabase.co/functions/v1/recommend-players
//   Body: { 
//     "player_id": "pro_player_uuid",
//     "limit": 5,
//     "regions": ["IN", "VN"]
//   }
//
// RESPONSE:
//   {
//     "source_player": { nickname, game_radar_score, ... },
//     "recommendations": [
//       { player_id, nickname, match_score, game_radar_score, ... }
//     ]
//   }
// ============================================================================

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// ============================================================================
// TYPES
// ============================================================================

interface RequestBody {
  player_id: string;
  limit?: number;
  regions?: string[];
  min_games?: number;
  max_results?: number;
}

interface Player {
  player_id: string;
  nickname: string;
  country: string;
  game: string;
  rank: string;
  game_radar_score: number;
  talent_score: number;
  win_rate: number;
  kda: number;
  games_played: number;
  skill_vector: number[];
  is_verified: boolean;
}

interface Recommendation extends Player {
  match_score: number;
  similarity_distance: number;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate match score percentage from cosine distance
 * Cosine distance range: 0 (identical) to 2 (opposite)
 * We convert to similarity: (2 - distance) / 2 * 100
 */
function calculateMatchScore(distance: number): number {
  const similarity = (2 - distance) / 2;
  return Math.round(similarity * 100);
}

/**
 * Format player data for response
 */
function formatPlayer(player: any): Player {
  return {
    player_id: player.player_id,
    nickname: player.nickname,
    country: player.country,
    game: player.game,
    rank: player.rank,
    game_radar_score: player.game_radar_score,
    talent_score: player.talent_score,
    win_rate: player.win_rate,
    kda: player.kda,
    games_played: player.games_played,
    skill_vector: player.skill_vector,
    is_verified: player.is_verified,
  };
}

// ============================================================================
// MAIN HANDLER
// ============================================================================

serve(async (req) => {
  // CORS Headers
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      },
    });
  }

  try {
    // ========================================================================
    // 1. PARSE REQUEST
    // ========================================================================
    const body: RequestBody = await req.json();
    const {
      player_id,
      limit = 5,
      regions = ['IN', 'VN'],
      min_games = 50,
      max_results = 10,
    } = body;

    if (!player_id) {
      return new Response(
        JSON.stringify({ error: 'player_id is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // ========================================================================
    // 2. INITIALIZE SUPABASE CLIENT
    // ========================================================================
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // ========================================================================
    // 3. FETCH SOURCE PLAYER (Professional)
    // ========================================================================
    const { data: sourcePlayer, error: sourceError } = await supabase
      .from('gold_analytics')
      .select(`
        player_id,
        nickname,
        country,
        game,
        rank,
        game_radar_score,
        talent_score,
        win_rate,
        kda,
        games_played,
        skill_vector,
        is_verified
      `)
      .eq('player_id', player_id)
      .single();

    if (sourceError || !sourcePlayer) {
      return new Response(
        JSON.stringify({ 
          error: 'Source player not found',
          details: sourceError?.message 
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate source player has skill_vector
    if (!sourcePlayer.skill_vector || sourcePlayer.skill_vector.length === 0) {
      return new Response(
        JSON.stringify({ 
          error: 'Source player does not have skill vector computed' 
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // ========================================================================
    // 4. FIND SIMILAR PLAYERS USING VECTOR SIMILARITY
    // ========================================================================
    // We use RPC call to leverage pgvector's cosine distance operator (<=>)
    // This is optimized with IVFFlat index for low-latency queries
    
    const vectorString = `[${sourcePlayer.skill_vector.join(',')}]`;

    const { data: similarPlayers, error: searchError } = await supabase.rpc(
      'search_similar_players',
      {
        query_vector: vectorString,
        match_threshold: 0.5,  // Only return players with distance < 0.5
        match_count: max_results,
        target_regions: regions,
        min_games_threshold: min_games,
      }
    );

    if (searchError) {
      // If RPC doesn't exist, fall back to manual query
      console.warn('RPC search_similar_players not found, using fallback query');
      
      const { data: fallbackPlayers, error: fallbackError } = await supabase
        .from('gold_analytics')
        .select(`
          player_id,
          nickname,
          country,
          game,
          rank,
          game_radar_score,
          talent_score,
          win_rate,
          kda,
          games_played,
          skill_vector,
          is_verified
        `)
        .in('country', regions)
        .gte('games_played', min_games)
        .neq('player_id', player_id)
        .not('skill_vector', 'is', null)
        .limit(100);  // Fetch more for client-side filtering

      if (fallbackError) {
        throw fallbackError;
      }

      // Calculate cosine distance manually
      const playersWithDistance = fallbackPlayers
        .map((player) => {
          const distance = cosineDistan ce(
            sourcePlayer.skill_vector,
            player.skill_vector
          );
          return { ...player, distance };
        })
        .filter((p) => p.distance < 0.5)
        .sort((a, b) => a.distance - b.distance)
        .slice(0, limit);

      const recommendations: Recommendation[] = playersWithDistance.map((p) => ({
        ...formatPlayer(p),
        match_score: calculateMatchScore(p.distance),
        similarity_distance: p.distance,
      }));

      return new Response(
        JSON.stringify({
          source_player: formatPlayer(sourcePlayer),
          recommendations,
          metadata: {
            total_found: recommendations.length,
            regions_searched: regions,
            min_games_filter: min_games,
            method: 'fallback_manual_calculation',
          },
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    // ========================================================================
    // 5. FORMAT AND RETURN RECOMMENDATIONS
    // ========================================================================
    const recommendations: Recommendation[] = (similarPlayers || [])
      .slice(0, limit)
      .map((p: any) => ({
        ...formatPlayer(p),
        match_score: calculateMatchScore(p.similarity_distance),
        similarity_distance: p.similarity_distance,
      }));

    return new Response(
      JSON.stringify({
        source_player: formatPlayer(sourcePlayer),
        recommendations,
        metadata: {
          total_found: recommendations.length,
          regions_searched: regions,
          min_games_filter: min_games,
          method: 'pgvector_rpc',
        },
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=300',  // Cache for 5 minutes
        },
      }
    );
  } catch (error) {
    console.error('Error in recommend-players function:', error);
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message,
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
});

// ============================================================================
// UTILITY: Cosine Distance Calculation (Fallback)
// ============================================================================

function cosineDista nce(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error('Vectors must have same dimension');
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);

  if (normA === 0 || normB === 0) {
    return 2;  // Maximum distance
  }

  const cosineSimilarity = dotProduct / (normA * normB);
  return 1 - cosineSimilarity;  // Convert similarity to distance
}
