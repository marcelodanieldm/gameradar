-- ============================================================================
-- SUPABASE RPC FUNCTION: Search Similar Players by Vector
-- ============================================================================
-- 
-- PURPOSE: Ultra-fast vector similarity search using pgvector's IVFFlat index
-- OPTIMIZATION: Low-latency queries optimized for recommendation system
--
-- USAGE:
--   SELECT * FROM search_similar_players(
--     query_vector := '[0.75, 0.68, 0.82, 0.91]',
--     match_threshold := 0.5,
--     match_count := 5,
--     target_regions := ARRAY['IN', 'VN'],
--     min_games_threshold := 50
--   );
--
-- RETURNS: Table with similar players and their similarity distance
-- ============================================================================

CREATE OR REPLACE FUNCTION search_similar_players(
  query_vector TEXT,
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  target_regions TEXT[] DEFAULT ARRAY['IN', 'VN'],
  min_games_threshold INT DEFAULT 50
)
RETURNS TABLE (
  player_id UUID,
  nickname TEXT,
  country TEXT,
  game TEXT,
  rank TEXT,
  game_radar_score NUMERIC,
  talent_score NUMERIC,
  win_rate NUMERIC,
  kda NUMERIC,
  games_played INT,
  skill_vector vector(4),
  is_verified BOOLEAN,
  similarity_distance FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ga.player_id,
    ga.nickname,
    ga.country,
    ga.game,
    ga.rank,
    ga.game_radar_score,
    ga.talent_score,
    ga.win_rate,
    ga.kda,
    ga.games_played,
    ga.skill_vector,
    ga.is_verified,
    (ga.skill_vector <=> query_vector::vector(4)) AS similarity_distance
  FROM gold_analytics ga
  WHERE 
    ga.skill_vector IS NOT NULL
    AND ga.country = ANY(target_regions)
    AND ga.games_played >= min_games_threshold
    AND (ga.skill_vector <=> query_vector::vector(4)) < match_threshold
  ORDER BY similarity_distance ASC
  LIMIT match_count;
END;
$$;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT EXECUTE ON FUNCTION search_similar_players TO anon, authenticated, service_role;

-- ============================================================================
-- PERFORMANCE INDEX (If not already created)
-- ============================================================================

-- Ensure IVFFlat index exists for fast vector similarity search
-- This should already exist from gold_analytics.sql, but adding as reminder

-- CREATE INDEX IF NOT EXISTS idx_gold_skill_vector 
-- ON gold_analytics 
-- USING ivfflat (skill_vector vector_cosine_ops)
-- WITH (lists = 100);

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Find players similar to Faker's skill vector
-- Assuming Faker's vector is [0.95, 0.88, 0.92, 0.98]
/*
SELECT 
  nickname,
  country,
  game_radar_score,
  similarity_distance,
  (100 - (similarity_distance * 50))::INT AS match_score_percentage
FROM search_similar_players(
  query_vector := '[0.95, 0.88, 0.92, 0.98]',
  match_threshold := 0.3,
  match_count := 5,
  target_regions := ARRAY['IN', 'VN', 'ID'],
  min_games_threshold := 100
);
*/

-- Example 2: Find top 10 most similar players across all regions
/*
SELECT 
  nickname,
  country,
  game,
  rank,
  game_radar_score,
  (1 - similarity_distance) * 100 AS similarity_percentage
FROM search_similar_players(
  query_vector := '[0.80, 0.75, 0.85, 0.90]',
  match_threshold := 0.5,
  match_count := 10,
  target_regions := ARRAY['IN', 'VN', 'KR', 'CN', 'JP'],
  min_games_threshold := 50
)
ORDER BY similarity_percentage DESC;
*/

-- Example 3: Get recommendation with detailed stats
/*
WITH source_player AS (
  SELECT skill_vector, nickname AS source_name
  FROM gold_analytics
  WHERE player_id = 'some-uuid'
)
SELECT 
  sp.nickname,
  sp.country,
  sp.game_radar_score,
  sp.talent_score,
  sp.win_rate,
  sp.kda,
  sp.games_played,
  ROUND((2 - sp.similarity_distance) / 2 * 100) AS match_score,
  src.source_name AS similar_to
FROM search_similar_players(
  query_vector := (SELECT skill_vector::TEXT FROM source_player),
  match_threshold := 0.4,
  match_count := 5,
  target_regions := ARRAY['IN', 'VN'],
  min_games_threshold := 50
) sp
CROSS JOIN source_player src
ORDER BY sp.similarity_distance ASC;
*/
