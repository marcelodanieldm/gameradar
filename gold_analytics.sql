-- ============================================================
-- GameRadar AI - Analytics Layer (Gold)
-- Función para calcular GameRadar Score con lógica regional
-- ============================================================

-- Extensión para vectores (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tabla gold_analytics (si no existe)
CREATE TABLE IF NOT EXISTS gold_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id TEXT NOT NULL,
    nickname TEXT NOT NULL,
    country_code TEXT NOT NULL,
    region TEXT NOT NULL,
    game TEXT NOT NULL,
    
    -- Métricas base
    win_rate DECIMAL(5,2),
    kda DECIMAL(5,2),
    games_played INTEGER,
    talent_score DECIMAL(5,2),
    
    -- GameRadar Score (calculado)
    gameradar_score DECIMAL(5,2) NOT NULL,

    -- Vector de habilidades (pgvector)
    -- Dimensiones: [kda, winrate, agresividad, versatilidad]
    skill_vector vector(4),
    
    -- Componentes del score (para transparencia)
    winrate_component DECIMAL(5,2),
    kda_component DECIMAL(5,2),
    volume_component DECIMAL(5,2),
    regional_multiplier DECIMAL(5,2),
    
    -- Metadata
    calculation_date TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    -- Índices para queries rápidas
    CONSTRAINT unique_player_calc UNIQUE (player_id, calculation_date)
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_gold_gameradar_score ON gold_analytics(gameradar_score DESC);
CREATE INDEX IF NOT EXISTS idx_gold_region ON gold_analytics(region);
CREATE INDEX IF NOT EXISTS idx_gold_calculation_date ON gold_analytics(calculation_date DESC);
CREATE INDEX IF NOT EXISTS idx_gold_player_id ON gold_analytics(player_id);
CREATE INDEX IF NOT EXISTS idx_gold_skill_vector
    ON gold_analytics USING ivfflat (skill_vector vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================
-- FUNCIÓN: calculate_gameradar_score_advanced
-- Calcula score personalizado por región con lógica de negocio
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_gameradar_score_advanced(
    p_win_rate DECIMAL,
    p_kda DECIMAL,
    p_games_played INTEGER,
    p_region TEXT,
    p_talent_score DECIMAL DEFAULT NULL
)
RETURNS TABLE (
    gameradar_score DECIMAL,
    winrate_component DECIMAL,
    kda_component DECIMAL,
    volume_component DECIMAL,
    regional_multiplier DECIMAL
) AS $$
DECLARE
    v_wr_component DECIMAL := 0;
    v_kda_component DECIMAL := 0;
    v_volume_component DECIMAL := 0;
    v_regional_mult DECIMAL := 1.0;
    v_final_score DECIMAL := 0;
    v_normalized_kda DECIMAL := 0;
    v_normalized_games DECIMAL := 0;
BEGIN
    -- ==============================================
    -- 1. COMPONENTE WIN RATE (Base: 40%)
    -- ==============================================
    IF p_win_rate IS NOT NULL THEN
        v_wr_component := LEAST(p_win_rate, 100) * 0.40;
    END IF;
    
    -- ==============================================
    -- 2. COMPONENTE KDA (Variable según región)
    -- ==============================================
    IF p_kda IS NOT NULL THEN
        -- Normalizar KDA: Asumimos rango 0-10, donde 5+ es excepcional
        -- Fórmula: (KDA / 10) * 100 = % score, luego aplicar peso
        v_normalized_kda := LEAST((p_kda / 10.0) * 100, 100);
        
        -- Peso según región:
        -- KR/CN/JP: KDA es crítico (30%)
        -- IN/VN/TH: KDA es secundario (15%)
        IF p_region IN ('KR', 'CN', 'JP') THEN
            v_kda_component := v_normalized_kda * 0.30;
        ELSE
            v_kda_component := v_normalized_kda * 0.15;
        END IF;
    END IF;
    
    -- ==============================================
    -- 3. COMPONENTE VOLUMEN DE PARTIDAS (Variable)
    -- ==============================================
    IF p_games_played IS NOT NULL THEN
        -- Normalizar games played: Asumimos 1000+ partidas = 100%
        -- Logarítmica para valorar primeras partidas más
        v_normalized_games := LEAST(
            (LN(GREATEST(p_games_played, 1)) / LN(1000)) * 100,
            100
        );
        
        -- Peso según región:
        -- KR/CN/JP: Volumen es secundario (10%)
        -- IN/VN/TH: Volumen es crítico (30%) - priorizan grinders
        IF p_region IN ('IN', 'VN', 'TH') THEN
            v_volume_component := v_normalized_games * 0.30;
        ELSE
            v_volume_component := v_normalized_games * 0.10;
        END IF;
    END IF;
    
    -- ==============================================
    -- 4. TALENT SCORE (Bonus: 20%)
    -- ==============================================
    IF p_talent_score IS NOT NULL THEN
        -- Ya está normalizado 0-100, aplicar peso directamente
        v_final_score := v_final_score + (p_talent_score * 0.20);
    END IF;
    
    -- ==============================================
    -- 5. MULTIPLICADOR REGIONAL
    -- ==============================================
    CASE p_region
        -- Alta competencia (Corea, China) = Multiplicador premium
        WHEN 'KR' THEN v_regional_mult := 1.20;
        WHEN 'CN' THEN v_regional_mult := 1.15;
        WHEN 'JP' THEN v_regional_mult := 1.10;
        
        -- Competencia estándar (Occidente)
        WHEN 'NA', 'EU', 'BR' THEN v_regional_mult := 1.05;
        
        -- Regiones emergentes (India, Vietnam, SEA)
        WHEN 'IN', 'VN', 'TH', 'PH', 'ID' THEN v_regional_mult := 1.0;
        
        -- Default
        ELSE v_regional_mult := 1.0;
    END CASE;
    
    -- ==============================================
    -- 6. CÁLCULO FINAL Y NORMALIZACIÓN
    -- ==============================================
    
    -- Sumar componentes base
    v_final_score := v_wr_component + v_kda_component + v_volume_component;
    
    -- Aplicar multiplicador regional
    v_final_score := v_final_score * v_regional_mult;
    
    -- Normalizar a rango 0-100
    v_final_score := LEAST(GREATEST(v_final_score, 0), 100);
    
    -- Retornar tabla con desglose
    RETURN QUERY SELECT
        ROUND(v_final_score, 2)::DECIMAL AS gameradar_score,
        ROUND(v_wr_component, 2)::DECIMAL AS winrate_component,
        ROUND(v_kda_component, 2)::DECIMAL AS kda_component,
        ROUND(v_volume_component, 2)::DECIMAL AS volume_component,
        v_regional_mult::DECIMAL AS regional_multiplier;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- FUNCIÓN: refresh_gold_analytics
-- Refresca toda la tabla gold_analytics desde silver_players
-- Ejecutar diariamente via pg_cron o trigger manual
-- ============================================================

CREATE OR REPLACE FUNCTION refresh_gold_analytics()
RETURNS TABLE (
    players_processed INTEGER,
    execution_time_ms INTEGER
) AS $$
DECLARE
    v_start_time TIMESTAMPTZ;
    v_end_time TIMESTAMPTZ;
    v_count INTEGER := 0;
BEGIN
    v_start_time := clock_timestamp();
    
    -- Truncar gold_analytics para recalcular desde cero
    -- (Alternativa: usar UPSERT para histórico)
    DELETE FROM gold_analytics 
    WHERE calculation_date = CURRENT_DATE;
    
    -- Insertar cálculos frescos desde silver_players
    INSERT INTO gold_analytics (
        player_id,
        nickname,
        country_code,
        region,
        game,
        win_rate,
        kda,
        games_played,
        talent_score,
        gameradar_score,
        winrate_component,
        kda_component,
        volume_component,
        regional_multiplier,
        calculation_date
    )
    SELECT
        sp.player_id,
        sp.nickname,
        sp.country_code,
        sp.region,
        sp.game,
        sp.win_rate,
        sp.kda,
        sp.games_played,
        sp.talent_score,
        -- Llamar función de cálculo
        (calc.gameradar_score),
        (calc.winrate_component),
        (calc.kda_component),
        (calc.volume_component),
        (calc.regional_multiplier),
        CURRENT_DATE
    FROM silver_players sp
    CROSS JOIN LATERAL calculate_gameradar_score_advanced(
        sp.win_rate,
        sp.kda,
        sp.games_played,
        sp.region,
        sp.talent_score
    ) AS calc
    WHERE sp.win_rate IS NOT NULL  -- Solo jugadores con datos mínimos
    ON CONFLICT (player_id, calculation_date)
    DO UPDATE SET
        nickname = EXCLUDED.nickname,
        win_rate = EXCLUDED.win_rate,
        kda = EXCLUDED.kda,
        games_played = EXCLUDED.games_played,
        talent_score = EXCLUDED.talent_score,
        gameradar_score = EXCLUDED.gameradar_score,
        winrate_component = EXCLUDED.winrate_component,
        kda_component = EXCLUDED.kda_component,
        volume_component = EXCLUDED.volume_component,
        regional_multiplier = EXCLUDED.regional_multiplier,
        last_updated = NOW();
    
    -- Contar registros procesados
    GET DIAGNOSTICS v_count = ROW_COUNT;
    
    v_end_time := clock_timestamp();
    
    -- Retornar stats
    RETURN QUERY SELECT
        v_count,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGER: Auto-actualizar gold_analytics al insertar/actualizar silver
-- ============================================================

CREATE OR REPLACE FUNCTION trigger_update_gold_analytics()
RETURNS TRIGGER AS $$
DECLARE
    v_calc RECORD;
BEGIN
    -- Calcular score para este jugador
    SELECT * INTO v_calc
    FROM calculate_gameradar_score_advanced(
        NEW.win_rate,
        NEW.kda,
        NEW.games_played,
        NEW.region,
        NEW.talent_score
    );
    
    -- Upsert en gold_analytics
    INSERT INTO gold_analytics (
        player_id,
        nickname,
        country_code,
        region,
        game,
        win_rate,
        kda,
        games_played,
        talent_score,
        gameradar_score,
        winrate_component,
        kda_component,
        volume_component,
        regional_multiplier,
        calculation_date
    ) VALUES (
        NEW.player_id,
        NEW.nickname,
        NEW.country_code,
        NEW.region,
        NEW.game,
        NEW.win_rate,
        NEW.kda,
        NEW.games_played,
        NEW.talent_score,
        v_calc.gameradar_score,
        v_calc.winrate_component,
        v_calc.kda_component,
        v_calc.volume_component,
        v_calc.regional_multiplier,
        CURRENT_DATE
    )
    ON CONFLICT (player_id, calculation_date)
    DO UPDATE SET
        nickname = EXCLUDED.nickname,
        win_rate = EXCLUDED.win_rate,
        kda = EXCLUDED.kda,
        games_played = EXCLUDED.games_played,
        talent_score = EXCLUDED.talent_score,
        gameradar_score = EXCLUDED.gameradar_score,
        winrate_component = EXCLUDED.winrate_component,
        kda_component = EXCLUDED.kda_component,
        volume_component = EXCLUDED.volume_component,
        regional_multiplier = EXCLUDED.regional_multiplier,
        last_updated = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger en silver_players
DROP TRIGGER IF EXISTS update_gold_on_silver_change ON silver_players;
CREATE TRIGGER update_gold_on_silver_change
    AFTER INSERT OR UPDATE OF win_rate, kda, games_played, talent_score
    ON silver_players
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_gold_analytics();

-- ============================================================
-- FUNCIÓN: search_similar_players
-- Búsqueda de vecinos cercanos usando cosine similarity
-- ============================================================

CREATE OR REPLACE FUNCTION search_similar_players(
    p_query_vector vector(4),
    p_limit INTEGER DEFAULT 10,
    p_country_code TEXT DEFAULT NULL,
    p_game TEXT DEFAULT NULL
)
RETURNS TABLE (
    player_id TEXT,
    nickname TEXT,
    country_code TEXT,
    region TEXT,
    game TEXT,
    similarity DOUBLE PRECISION,
    gameradar_score DECIMAL,
    win_rate DECIMAL,
    kda DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ga.player_id,
        ga.nickname,
        ga.country_code,
        ga.region,
        ga.game,
        (1 - (ga.skill_vector <=> p_query_vector)) AS similarity,
        ga.gameradar_score,
        ga.win_rate,
        ga.kda
    FROM gold_analytics ga
    WHERE ga.skill_vector IS NOT NULL
      AND (p_country_code IS NULL OR ga.country_code = p_country_code)
      AND (p_game IS NULL OR ga.game = p_game)
    ORDER BY ga.skill_vector <=> p_query_vector
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================
-- VISTAS ANALÍTICAS
-- ============================================================

-- Vista: Top 100 jugadores globales
CREATE OR REPLACE VIEW vw_top_players_global AS
SELECT
    nickname,
    country_code,
    region,
    game,
    gameradar_score,
    win_rate,
    kda,
    games_played,
    regional_multiplier,
    calculation_date
FROM gold_analytics
WHERE calculation_date = CURRENT_DATE
ORDER BY gameradar_score DESC
LIMIT 100;

-- Vista: Top jugadores por región
CREATE OR REPLACE VIEW vw_top_players_by_region AS
SELECT
    region,
    nickname,
    country_code,
    gameradar_score,
    win_rate,
    kda,
    games_played,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY gameradar_score DESC) as rank_in_region
FROM gold_analytics
WHERE calculation_date = CURRENT_DATE
ORDER BY region, gameradar_score DESC;

-- Vista: Comparación regional de componentes
CREATE OR REPLACE VIEW vw_regional_score_breakdown AS
SELECT
    region,
    COUNT(*) as total_players,
    ROUND(AVG(gameradar_score), 2) as avg_score,
    ROUND(AVG(winrate_component), 2) as avg_wr_component,
    ROUND(AVG(kda_component), 2) as avg_kda_component,
    ROUND(AVG(volume_component), 2) as avg_volume_component,
    AVG(regional_multiplier) as avg_multiplier
FROM gold_analytics
WHERE calculation_date = CURRENT_DATE
GROUP BY region
ORDER BY avg_score DESC;

-- ============================================================
-- FUNCIONES DE CONSULTA RÁPIDA
-- ============================================================

-- Función: Obtener score de un jugador específico
CREATE OR REPLACE FUNCTION get_player_score(p_player_id TEXT)
RETURNS TABLE (
    nickname TEXT,
    gameradar_score DECIMAL,
    global_rank BIGINT,
    regional_rank BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH global_ranks AS (
        SELECT
            player_id,
            nickname,
            gameradar_score,
            region,
            ROW_NUMBER() OVER (ORDER BY gameradar_score DESC) as global_rank,
            ROW_NUMBER() OVER (PARTITION BY region ORDER BY gameradar_score DESC) as regional_rank
        FROM gold_analytics
        WHERE calculation_date = CURRENT_DATE
    )
    SELECT
        gr.nickname,
        gr.gameradar_score,
        gr.global_rank,
        gr.regional_rank
    FROM global_ranks gr
    WHERE gr.player_id = p_player_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PROGRAMACIÓN DIARIA (Requiere pg_cron extension)
-- ============================================================

-- Habilitar pg_cron (ejecutar como superuser)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Programar ejecución diaria a las 02:00 AM UTC
-- SELECT cron.schedule(
--     'refresh-gameradar-analytics',
--     '0 2 * * *',  -- 02:00 AM diario
--     'SELECT refresh_gold_analytics();'
-- );

-- ============================================================
-- QUERIES DE PRUEBA Y VALIDACIÓN
-- ============================================================

-- Test 1: Calcular score manualmente para un jugador
/*
SELECT * FROM calculate_gameradar_score_advanced(
    65.5,  -- win_rate
    4.2,   -- kda
    500,   -- games_played
    'KR',  -- region
    85.0   -- talent_score
);
*/

-- Test 2: Refrescar analytics y ver stats
/*
SELECT * FROM refresh_gold_analytics();
*/

-- Test 3: Ver top 10 global
/*
SELECT * FROM vw_top_players_global LIMIT 10;
*/

-- Test 4: Ver breakdown por región
/*
SELECT * FROM vw_regional_score_breakdown;
*/

-- Test 5: Buscar score de jugador específico
/*
SELECT * FROM get_player_score('faker_t1');
*/

-- ============================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================

COMMENT ON FUNCTION calculate_gameradar_score_advanced IS 
'Calcula GameRadar Score con lógica regional personalizada:
- KR: Win Rate x1.2, KDA 30%, Volume 10%
- IN/VN: Volume 30%, KDA 15%
- Normalizado 0-100';

COMMENT ON FUNCTION refresh_gold_analytics IS
'Refresca gold_analytics desde silver_players. 
Ejecutar diariamente via pg_cron o manualmente.';

COMMENT ON TABLE gold_analytics IS
'Capa Gold: Analytics de GameRadar Score calculado con componentes regionales.';

COMMENT ON VIEW vw_top_players_global IS
'Top 100 jugadores globales ordenados por GameRadar Score.';
