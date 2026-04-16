-- =====================================================
-- TABLA DE LOGS PARA MULTI-REGION INGESTOR
-- =====================================================
-- Crear tabla para almacenar logs de ingesta

CREATE TABLE IF NOT EXISTS ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    duration_seconds NUMERIC(10, 2),
    total_players INTEGER NOT NULL DEFAULT 0,
    successful INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    success_rate NUMERIC(5, 2),
    total_fallbacks INTEGER NOT NULL DEFAULT 0,
    source_metrics JSONB,
    errors TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para queries eficientes
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_session_id ON ingestion_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_created_at ON ingestion_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_success_rate ON ingestion_logs(success_rate);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_ingestion_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ingestion_logs_updated_at
    BEFORE UPDATE ON ingestion_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_ingestion_logs_updated_at();

-- =====================================================
-- VISTAS ANALÍTICAS
-- =====================================================

-- Vista: Métricas globales de ingesta
CREATE OR REPLACE VIEW v_ingestion_global_metrics AS
SELECT
    COUNT(*) AS total_sessions,
    SUM(total_players) AS total_players_ingested,
    SUM(successful) AS total_successful,
    SUM(failed) AS total_failed,
    ROUND(AVG(success_rate), 2) AS avg_success_rate,
    ROUND(AVG(duration_seconds), 2) AS avg_duration_seconds,
    SUM(total_fallbacks) AS total_fallbacks,
    MIN(created_at) AS first_ingestion,
    MAX(created_at) AS last_ingestion
FROM ingestion_logs;

-- Vista: Métricas por fuente
CREATE OR REPLACE VIEW v_ingestion_source_metrics AS
SELECT
    source->>'source' AS source_name,
    COUNT(*) AS sessions_used,
    SUM((source->>'requests')::INTEGER) AS total_requests,
    SUM((source->>'successes')::INTEGER) AS total_successes,
    SUM((source->>'failures')::INTEGER) AS total_failures,
    ROUND(
        AVG((source->>'success_rate')::NUMERIC), 
        2
    ) AS avg_success_rate,
    ROUND(
        AVG((source->>'avg_duration_ms')::NUMERIC), 
        2
    ) AS avg_duration_ms
FROM ingestion_logs,
     LATERAL jsonb_array_elements(
         CASE 
             WHEN jsonb_typeof(source_metrics) = 'object' 
             THEN jsonb_build_array(source_metrics)
             ELSE source_metrics
         END
     ) AS source
WHERE source_metrics IS NOT NULL
GROUP BY source->>'source'
ORDER BY total_requests DESC;

-- Vista: Tendencia diaria
CREATE OR REPLACE VIEW v_ingestion_daily_trend AS
SELECT
    DATE(created_at) AS ingestion_date,
    COUNT(*) AS sessions,
    SUM(total_players) AS players,
    SUM(successful) AS successful,
    SUM(failed) AS failed,
    ROUND(AVG(success_rate), 2) AS avg_success_rate,
    ROUND(AVG(duration_seconds), 2) AS avg_duration
FROM ingestion_logs
GROUP BY DATE(created_at)
ORDER BY ingestion_date DESC;

-- Vista: Últimas 10 sesiones
CREATE OR REPLACE VIEW v_ingestion_recent_sessions AS
SELECT
    session_id,
    start_time,
    end_time,
    duration_seconds,
    total_players,
    successful,
    failed,
    success_rate,
    total_fallbacks,
    created_at
FROM ingestion_logs
ORDER BY created_at DESC
LIMIT 10;

-- =====================================================
-- FUNCIONES HELPER
-- =====================================================

-- Función: Obtener métricas de una sesión específica
CREATE OR REPLACE FUNCTION get_session_metrics(p_session_id UUID)
RETURNS TABLE (
    session_id UUID,
    total_players INTEGER,
    successful INTEGER,
    failed INTEGER,
    success_rate NUMERIC,
    duration_seconds NUMERIC,
    sources_used TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        il.session_id,
        il.total_players,
        il.successful,
        il.failed,
        il.success_rate,
        il.duration_seconds,
        ARRAY(
            SELECT jsonb_object_keys(il.source_metrics)
        ) AS sources_used
    FROM ingestion_logs il
    WHERE il.session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Función: Limpiar logs antiguos (mantener últimos 90 días)
CREATE OR REPLACE FUNCTION cleanup_old_ingestion_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ingestion_logs
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función: Obtener health status del sistema de ingesta
CREATE OR REPLACE FUNCTION get_ingestion_health_status()
RETURNS TABLE (
    status TEXT,
    last_session_time TIMESTAMPTZ,
    hours_since_last_session NUMERIC,
    avg_success_rate_24h NUMERIC,
    total_players_24h INTEGER,
    active_sources INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN MAX(created_at) > NOW() - INTERVAL '12 hours' AND AVG(success_rate) > 80.0 
            THEN 'healthy'
            WHEN MAX(created_at) > NOW() - INTERVAL '24 hours' AND AVG(success_rate) > 60.0 
            THEN 'degraded'
            ELSE 'critical'
        END AS status,
        MAX(created_at) AS last_session_time,
        ROUND(
            EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600, 
            2
        ) AS hours_since_last_session,
        ROUND(AVG(CASE 
            WHEN created_at > NOW() - INTERVAL '24 hours' 
            THEN success_rate 
        END), 2) AS avg_success_rate_24h,
        SUM(CASE 
            WHEN created_at > NOW() - INTERVAL '24 hours' 
            THEN total_players 
            ELSE 0 
        END)::INTEGER AS total_players_24h,
        (
            SELECT COUNT(DISTINCT jsonb_object_keys(source_metrics))
            FROM ingestion_logs
            WHERE created_at > NOW() - INTERVAL '24 hours'
        )::INTEGER AS active_sources
    FROM ingestion_logs;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS
-- =====================================================

COMMENT ON TABLE ingestion_logs IS 'Logs detallados de sesiones de ingesta multi-región';
COMMENT ON COLUMN ingestion_logs.session_id IS 'UUID único de la sesión';
COMMENT ON COLUMN ingestion_logs.source_metrics IS 'JSONB con métricas por fuente';
COMMENT ON COLUMN ingestion_logs.errors IS 'Array de errores encontrados';

COMMENT ON VIEW v_ingestion_global_metrics IS 'Métricas agregadas de todas las sesiones';
COMMENT ON VIEW v_ingestion_source_metrics IS 'Performance por fuente de datos';
COMMENT ON VIEW v_ingestion_daily_trend IS 'Tendencia diaria de ingestas';

COMMENT ON FUNCTION get_session_metrics IS 'Obtener métricas detalladas de una sesión';
COMMENT ON FUNCTION cleanup_old_ingestion_logs IS 'Limpiar logs antiguos para mantener DB limpia';
COMMENT ON FUNCTION get_ingestion_health_status IS 'Health check del sistema de ingesta';

-- =====================================================
-- GRANTS (ajustar según tus roles)
-- =====================================================

-- GRANT SELECT, INSERT ON ingestion_logs TO service_role;
-- GRANT SELECT ON v_ingestion_global_metrics TO anon, authenticated;
-- GRANT SELECT ON v_ingestion_source_metrics TO anon, authenticated;
-- GRANT EXECUTE ON FUNCTION get_ingestion_health_status TO anon, authenticated;

-- =====================================================
-- EJEMPLO DE QUERIES
-- =====================================================

-- Ver métricas globales
-- SELECT * FROM v_ingestion_global_metrics;

-- Ver performance por fuente
-- SELECT * FROM v_ingestion_source_metrics;

-- Ver tendencia diaria
-- SELECT * FROM v_ingestion_daily_trend;

-- Health check
-- SELECT * FROM get_ingestion_health_status();

-- Limpiar logs antiguos (mantener 90 días)
-- SELECT cleanup_old_ingestion_logs(90);
