-- =====================================================
-- GameRadar AI - Supabase Database Schema
-- Arquitectura Bronze/Silver/Gold (Medallion Architecture)
-- Soporte completo para Unicode (Hindi, Chino, Coreano)
-- =====================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para búsqueda de texto difusa

-- =====================================================
-- CAPA BRONZE: Datos crudos sin procesar
-- =====================================================

CREATE TABLE bronze_raw_data (
    id BIGSERIAL PRIMARY KEY,
    raw_data JSONB NOT NULL,
    source VARCHAR(100) NOT NULL, -- 'liquipedia', 'opgg', etc.
    source_url TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices para búsqueda rápida
    CONSTRAINT check_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Índices para la capa Bronze
CREATE INDEX idx_bronze_source ON bronze_raw_data(source);
CREATE INDEX idx_bronze_status ON bronze_raw_data(processing_status);
CREATE INDEX idx_bronze_scraped_at ON bronze_raw_data(scraped_at DESC);
CREATE INDEX idx_bronze_raw_data_gin ON bronze_raw_data USING gin(raw_data);

COMMENT ON TABLE bronze_raw_data IS 'Capa Bronze: Datos crudos sin procesar del scraping';

-- =====================================================
-- CAPA SILVER: Datos normalizados y validados
-- =====================================================

CREATE TABLE silver_players (
    id BIGSERIAL PRIMARY KEY,
    bronze_id BIGINT REFERENCES bronze_raw_data(id) ON DELETE SET NULL,
    
    -- Información del jugador (con soporte Unicode completo)
    nickname VARCHAR(100) NOT NULL,
    game VARCHAR(20) NOT NULL, -- 'LOL', 'VAL', 'DOTA2', etc.
    country VARCHAR(2) NOT NULL, -- Código ISO de país
    server VARCHAR(50) NOT NULL,
    
    -- Ranking
    rank VARCHAR(50),
    rank_numeric INTEGER,
    
    -- Estadísticas (JSONB para flexibilidad)
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Top campeones
    top_champions JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Metadatos
    profile_url TEXT NOT NULL,
    data_quality_score DECIMAL(3,2) DEFAULT 1.0 CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    
    -- Timestamps
    normalized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_player_game UNIQUE (nickname, game, server),
    CONSTRAINT check_country_code CHECK (LENGTH(country) = 2)
);

-- Índices para la capa Silver
CREATE INDEX idx_silver_nickname ON silver_players(nickname);
CREATE INDEX idx_silver_game ON silver_players(game);
CREATE INDEX idx_silver_country ON silver_players(country);
CREATE INDEX idx_silver_rank_numeric ON silver_players(rank_numeric DESC) WHERE rank_numeric IS NOT NULL;
CREATE INDEX idx_silver_stats_gin ON silver_players USING gin(stats);
CREATE INDEX idx_silver_top_champions_gin ON silver_players USING gin(top_champions);
CREATE INDEX idx_silver_normalized_at ON silver_players(normalized_at DESC);

-- Índice para búsqueda de texto difusa en nickname (soporte Unicode)
CREATE INDEX idx_silver_nickname_trgm ON silver_players USING gin(nickname gin_trgm_ops);

COMMENT ON TABLE silver_players IS 'Capa Silver: Datos normalizados y validados de jugadores';
COMMENT ON COLUMN silver_players.nickname IS 'Nickname del jugador con soporte Unicode (Hindi, Chino, Coreano)';
COMMENT ON COLUMN silver_players.stats IS 'Estadísticas: {win_rate, kda, kills_avg, deaths_avg, assists_avg, games_analyzed}';
COMMENT ON COLUMN silver_players.top_champions IS 'Array de top 3 campeones: [{name, games_played, win_rate}]';

-- =====================================================
-- CAPA GOLD: Datos enriquecidos y verificados
-- =====================================================

CREATE TABLE gold_verified_players (
    id BIGSERIAL PRIMARY KEY,
    silver_id BIGINT REFERENCES silver_players(id) ON DELETE CASCADE,
    
    -- Todos los campos de silver (denormalizados para performance)
    nickname VARCHAR(100) NOT NULL,
    game VARCHAR(20) NOT NULL,
    country VARCHAR(2) NOT NULL,
    server VARCHAR(50) NOT NULL,
    rank VARCHAR(50),
    rank_numeric INTEGER,
    stats JSONB NOT NULL,
    top_champions JSONB NOT NULL,
    profile_url TEXT NOT NULL,
    
    -- Enriquecimiento
    enrichment_notes TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verification_date TIMESTAMP WITH TIME ZONE,
    
    -- Score de talento (calculado)
    talent_score DECIMAL(5,2),
    
    -- GameRadar Score (WinRate 40%, KDA 30%, dificultad región 30%)
    gameradar_score DECIMAL(5,2),
    
    -- Timestamps
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_gold_player UNIQUE (nickname, game, server)
);

-- Índices para la capa Gold
CREATE INDEX idx_gold_nickname ON gold_verified_players(nickname);
CREATE INDEX idx_gold_game ON gold_verified_players(game);
CREATE INDEX idx_gold_country ON gold_verified_players(country);
CREATE INDEX idx_gold_talent_score ON gold_verified_players(talent_score DESC) WHERE talent_score IS NOT NULL;
CREATE INDEX idx_gold_verified ON gold_verified_players(is_verified);

COMMENT ON TABLE gold_verified_players IS 'Capa Gold: Datos enriquecidos y verificados manualmente';
COMMENT ON COLUMN gold_verified_players.talent_score IS 'Score de talento calculado (0-100) basado en stats';
COMMENT ON COLUMN gold_verified_players.gameradar_score IS 'GameRadar Score calculado con WinRate, KDA y dificultad regional';

-- =====================================================
-- FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para silver_players
CREATE TRIGGER update_silver_players_updated_at 
    BEFORE UPDATE ON silver_players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para gold_verified_players
CREATE TRIGGER update_gold_verified_players_updated_at
    BEFORE UPDATE ON gold_verified_players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Función de normalización: Bronze -> Silver
-- =====================================================

CREATE OR REPLACE FUNCTION normalize_bronze_to_silver()
RETURNS TRIGGER AS $$
DECLARE
    player_data JSONB;
    nickname_val VARCHAR(100);
    game_val VARCHAR(20);
    country_val VARCHAR(2);
    server_val VARCHAR(50);
    rank_val VARCHAR(50);
    stats_val JSONB;
    top_champions_val JSONB;
    profile_url_val TEXT;
BEGIN
    -- Solo procesar si el status es 'pending'
    IF NEW.processing_status = 'pending' THEN
        BEGIN
            -- Extraer datos del JSONB
            player_data := NEW.raw_data;
            
            -- Validar que tenga los campos mínimos requeridos
            IF player_data ? 'nickname' AND player_data ? 'game' THEN
                
                nickname_val := player_data->>'nickname';
                game_val := player_data->>'game';
                country_val := COALESCE(player_data->>'country', 'XX');
                server_val := COALESCE(player_data->>'server', 'UNKNOWN');
                rank_val := player_data->>'rank';
                stats_val := COALESCE(player_data->'stats', '{}'::jsonb);
                top_champions_val := COALESCE(player_data->'top_champions', '[]'::jsonb);
                profile_url_val := COALESCE(player_data->>'profile_url', '');
                
                -- Insertar en Silver (o actualizar si ya existe)
                INSERT INTO silver_players (
                    bronze_id,
                    nickname,
                    game,
                    country,
                    server,
                    rank,
                    stats,
                    top_champions,
                    profile_url
                )
                VALUES (
                    NEW.id,
                    nickname_val,
                    game_val,
                    country_val,
                    server_val,
                    rank_val,
                    stats_val,
                    top_champions_val,
                    profile_url_val
                )
                ON CONFLICT (nickname, game, server) 
                DO UPDATE SET
                    bronze_id = EXCLUDED.bronze_id,
                    rank = EXCLUDED.rank,
                    stats = EXCLUDED.stats,
                    top_champions = EXCLUDED.top_champions,
                    profile_url = EXCLUDED.profile_url,
                    updated_at = NOW();
                
                -- Actualizar status a 'completed'
                NEW.processing_status := 'completed';
                
            ELSE
                -- Si faltan campos requeridos, marcar como failed
                NEW.processing_status := 'failed';
                NEW.error_message := 'Campos requeridos faltantes: nickname o game';
            END IF;
            
        EXCEPTION WHEN OTHERS THEN
            -- En caso de error, marcar como failed
            NEW.processing_status := 'failed';
            NEW.error_message := SQLERRM;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que ejecuta la normalización al insertar en Bronze
CREATE TRIGGER trigger_normalize_bronze_to_silver
    BEFORE INSERT ON bronze_raw_data
    FOR EACH ROW
    EXECUTE FUNCTION normalize_bronze_to_silver();

COMMENT ON FUNCTION normalize_bronze_to_silver() IS 
    'Función automática que normaliza datos de Bronze a Silver al insertar';

-- =====================================================
-- Función para calcular Talent Score
-- =====================================================

CREATE OR REPLACE FUNCTION calculate_talent_score(
    win_rate DECIMAL,
    kda DECIMAL,
    rank_numeric INTEGER
)
RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL := 0;
BEGIN
    -- Componente de Win Rate (0-40 puntos)
    score := score + (win_rate * 0.4);
    
    -- Componente de KDA (0-30 puntos)
    -- KDA normalizado: 3.0+ = 30 pts, 2.0 = 20 pts, 1.0 = 10 pts
    score := score + LEAST(kda * 10, 30);
    
    -- Componente de Rank (0-30 puntos)
    -- Rank numérico: más alto = mejor
    IF rank_numeric IS NOT NULL THEN
        score := score + LEAST(rank_numeric / 10.0, 30);
    END IF;
    
    -- Normalizar a escala 0-100
    RETURN LEAST(score, 100);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_talent_score IS 
    'Calcula un score de talento (0-100) basado en Win Rate, KDA y Rank';

-- =====================================================
-- Función para calcular GameRadar Score
-- =====================================================

CREATE OR REPLACE FUNCTION calculate_gameradar_score(
    win_rate DECIMAL,
    kda DECIMAL,
    country_code VARCHAR(2)
)
RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL := 0;
    win_rate_component DECIMAL := 0;
    kda_component DECIMAL := 0;
    region_component DECIMAL := 0;
    region_multiplier DECIMAL := 1.0;
    normalized_kda DECIMAL := 0;
BEGIN
    -- Normalización de KDA a 0-100 (KDA 5.0+ => 100)
    normalized_kda := LEAST(COALESCE(kda, 0) * 20, 100);

    -- Componentes ponderados
    win_rate_component := COALESCE(win_rate, 0) * 0.4; -- 40%
    kda_component := normalized_kda * 0.3; -- 30%

    -- Dificultad regional (30%)
    -- Corea = 1.2, India = 1.0, default = 1.0
    region_multiplier := CASE UPPER(country_code)
        WHEN 'KR' THEN 1.2
        WHEN 'IN' THEN 1.0
        ELSE 1.0
    END;

    region_component := 30 * region_multiplier;

    score := win_rate_component + kda_component + region_component;

    -- Normalizar a escala 0-100
    RETURN LEAST(score, 100);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_gameradar_score IS 
    'Calcula el GameRadarScore con WinRate 40%, KDA 30%, dificultad región 30%';

-- =====================================================
-- Trigger para persistir GameRadar Score en Gold
-- =====================================================

CREATE OR REPLACE FUNCTION set_gameradar_score_on_gold()
RETURNS TRIGGER AS $$
DECLARE
    win_rate_val DECIMAL := 0;
    kda_val DECIMAL := 0;
BEGIN
    win_rate_val := COALESCE((NEW.stats->>'win_rate')::DECIMAL, 0);
    kda_val := COALESCE((NEW.stats->>'kda')::DECIMAL, 0);

    NEW.gameradar_score := calculate_gameradar_score(
        win_rate_val,
        kda_val,
        NEW.country
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_gold_gameradar_score
    BEFORE INSERT OR UPDATE ON gold_verified_players
    FOR EACH ROW
    EXECUTE FUNCTION set_gameradar_score_on_gold();

-- =====================================================
-- Vista: Top Players por país
-- =====================================================

CREATE OR REPLACE VIEW vw_top_players_by_country AS
SELECT 
    country,
    game,
    nickname,
    rank,
    (stats->>'win_rate')::DECIMAL as win_rate,
    (stats->>'kda')::DECIMAL as kda,
    profile_url,
    ROW_NUMBER() OVER (PARTITION BY country, game ORDER BY rank_numeric DESC NULLS LAST) as rank_in_country
FROM silver_players
WHERE data_quality_score >= 0.7
ORDER BY country, game, rank_numeric DESC NULLS LAST;

COMMENT ON VIEW vw_top_players_by_country IS 
    'Vista de top players rankeados por país y juego';

-- =====================================================
-- Vista: Estadísticas por región
-- =====================================================

CREATE OR REPLACE VIEW vw_stats_by_region AS
SELECT 
    country,
    game,
    COUNT(*) as total_players,
    AVG((stats->>'win_rate')::DECIMAL) as avg_win_rate,
    AVG((stats->>'kda')::DECIMAL) as avg_kda,
    MAX((stats->>'win_rate')::DECIMAL) as max_win_rate,
    MAX((stats->>'kda')::DECIMAL) as max_kda
FROM silver_players
GROUP BY country, game
ORDER BY total_players DESC;

COMMENT ON VIEW vw_stats_by_region IS 
    'Estadísticas agregadas de jugadores por región y juego';

-- =====================================================
-- Tabla de auditoría
-- =====================================================

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);

-- =====================================================
-- Datos iniciales / Seeds
-- =====================================================

-- Insertar un registro de ejemplo para testing
INSERT INTO bronze_raw_data (raw_data, source, source_url) 
VALUES (
    '{
        "nickname": "Faker",
        "game": "LOL",
        "country": "KR",
        "server": "KR",
        "rank": "Challenger",
        "stats": {
            "win_rate": 65.5,
            "kda": 4.8,
            "games_analyzed": 100
        },
        "top_champions": [
            {"name": "Azir", "games_played": 50, "win_rate": 70.0},
            {"name": "LeBlanc", "games_played": 30, "win_rate": 65.0},
            {"name": "Orianna", "games_played": 20, "win_rate": 60.0}
        ],
        "profile_url": "https://kr.op.gg/summoners/kr/Faker"
    }'::jsonb,
    'opgg',
    'https://kr.op.gg/summoners/kr/Faker'
);

-- =====================================================
-- Permisos de Row Level Security (RLS)
-- =====================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE bronze_raw_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold_verified_players ENABLE ROW LEVEL SECURITY;

-- Política: Permitir lectura a todos los usuarios autenticados
CREATE POLICY "Enable read access for authenticated users" ON bronze_raw_data
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable read access for authenticated users" ON silver_players
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable read access for authenticated users" ON gold_verified_players
    FOR SELECT USING (auth.role() = 'authenticated');

-- Política: Permitir escritura solo a admin
CREATE POLICY "Enable write access for admin only" ON bronze_raw_data
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Enable write access for admin only" ON silver_players
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Enable write access for admin only" ON gold_verified_players
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- =====================================================
-- SPRINT 3: CASHFLOW Y ENGAGEMENT
-- Tablas para Pagos Regionales y Sistema Talent-Ping
-- =====================================================

-- =====================================================
-- PAYMENT TRANSACTIONS
-- Soporta Razorpay (India/UPI) y Stripe (Global)
-- =====================================================
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL, -- INR, USD, KRW, JPY, etc.
    region VARCHAR(50) NOT NULL, -- india, korea, japan, global, etc.
    
    -- Gateway information
    gateway VARCHAR(20) NOT NULL, -- 'razorpay' or 'stripe'
    order_id VARCHAR(255), -- Razorpay order_id or Stripe session_id
    payment_id VARCHAR(255), -- Payment ID after completion
    payment_method VARCHAR(50), -- upi, card, netbanking, kakao_pay, etc.
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, completed, failed, refunded
    error_message TEXT,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_payment_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded'))
);

-- Índices para búsqueda rápida de transacciones
CREATE INDEX idx_payment_user_id ON payment_transactions(user_id);
CREATE INDEX idx_payment_status ON payment_transactions(status);
CREATE INDEX idx_payment_gateway ON payment_transactions(gateway);
CREATE INDEX idx_payment_created_at ON payment_transactions(created_at DESC);
CREATE INDEX idx_payment_region ON payment_transactions(region);

COMMENT ON TABLE payment_transactions IS 'Sprint 3: Transacciones de pago regionales (Razorpay/Stripe)';


-- =====================================================
-- USER SUBSCRIPTIONS
-- Gestión de suscripciones premium
-- =====================================================
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Subscription details
    subscription_type VARCHAR(50) NOT NULL, -- free, premium, elite, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, expired, cancelled
    
    -- Features access
    features JSONB, -- { "talent_ping": true, "advanced_analytics": true, etc. }
    
    -- Timestamps
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_subscription_status CHECK (status IN ('active', 'expired', 'cancelled'))
);

CREATE INDEX idx_subscription_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_subscription_status ON user_subscriptions(status);
CREATE INDEX idx_subscription_expires_at ON user_subscriptions(expires_at);

COMMENT ON TABLE user_subscriptions IS 'Sprint 3: Gestión de suscripciones de usuarios';


-- =====================================================
-- TALENT PING SUBSCRIPTIONS
-- Sistema de alertas "Talent-Ping" con preferencias culturales
-- =====================================================
CREATE TABLE talent_ping_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Regional preferences
    region VARCHAR(50) NOT NULL, -- india, vietnam, korea, japan, china, global
    
    -- Notification channels (culturally adapted)
    notification_channels TEXT[] NOT NULL, -- ['email', 'whatsapp', 'telegram', 'in_app']
    
    -- Contact information (encrypted in production)
    email VARCHAR(255),
    whatsapp_number VARCHAR(20), -- For India/Vietnam
    telegram_id VARCHAR(100), -- For India/Vietnam
    
    -- Alert preferences
    alert_frequency VARCHAR(20) DEFAULT 'instant', -- instant, daily, weekly
    alert_criteria JSONB, -- Custom criteria for alerts
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    last_alert_sent_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_alert_frequency CHECK (alert_frequency IN ('instant', 'daily', 'weekly'))
);

CREATE INDEX idx_talent_ping_user_id ON talent_ping_subscriptions(user_id);
CREATE INDEX idx_talent_ping_region ON talent_ping_subscriptions(region);
CREATE INDEX idx_talent_ping_active ON talent_ping_subscriptions(is_active);
CREATE INDEX idx_talent_ping_frequency ON talent_ping_subscriptions(alert_frequency);

COMMENT ON TABLE talent_ping_subscriptions IS 'Sprint 3: Subscripciones a alertas Talent-Ping (WhatsApp/Telegram/Email)';


-- =====================================================
-- TALENT PING ALERTS LOG
-- Historial de alertas enviadas
-- =====================================================
CREATE TABLE talent_ping_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    
    -- Player information
    player_name VARCHAR(255) NOT NULL,
    player_position VARCHAR(50),
    similarity_score DECIMAL(5, 4), -- 0.0000 to 1.0000
    
    -- Alert details
    channels_sent TEXT[], -- ['whatsapp', 'email', etc.]
    delivery_status JSONB, -- { "whatsapp": true, "email": false, etc. }
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- User interaction
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_alerts_user_id ON talent_ping_alerts(user_id);
CREATE INDEX idx_alerts_sent_at ON talent_ping_alerts(sent_at DESC);
CREATE INDEX idx_alerts_player ON talent_ping_alerts(player_name);

COMMENT ON TABLE talent_ping_alerts IS 'Sprint 3: Historial de alertas Talent-Ping enviadas';


-- =====================================================
-- REGIONAL PAYMENT METRICS (Analytics)
-- Métricas de conversión por región para optimizar pagos
-- =====================================================
CREATE TABLE regional_payment_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Regional data
    region VARCHAR(50) NOT NULL,
    gateway VARCHAR(20) NOT NULL,
    payment_method VARCHAR(50),
    
    -- Metrics
    total_transactions INT DEFAULT 0,
    successful_transactions INT DEFAULT 0,
    failed_transactions INT DEFAULT 0,
    total_revenue DECIMAL(15, 2) DEFAULT 0,
    
    -- Conversion rates
    conversion_rate DECIMAL(5, 4), -- Calculated: successful/total
    
    -- Time period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_payment_metrics_region ON regional_payment_metrics(region);
CREATE INDEX idx_payment_metrics_period ON regional_payment_metrics(period_start, period_end);

COMMENT ON TABLE regional_payment_metrics IS 'Sprint 3: Métricas de conversión de pagos por región';


-- =====================================================
-- RLS (Row Level Security) Policies - Sprint 3
-- =====================================================

ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE talent_ping_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE talent_ping_alerts ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own payments" ON payment_transactions
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "Users can view own subscription" ON user_subscriptions
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "Users can manage own talent ping subscription" ON talent_ping_subscriptions
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can view own alerts" ON talent_ping_alerts
    FOR SELECT USING (user_id = auth.uid()::text);

-- Admin access
CREATE POLICY "Admin can view all payments" ON payment_transactions
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Admin can manage all subscriptions" ON user_subscriptions
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');


-- =====================================================
-- FUNCTIONS FOR SPRINT 3
-- =====================================================

-- Function to update payment metrics
CREATE OR REPLACE FUNCTION update_payment_metrics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        INSERT INTO regional_payment_metrics (
            region, 
            gateway, 
            payment_method,
            total_transactions,
            successful_transactions,
            total_revenue,
            period_start,
            period_end
        )
        VALUES (
            NEW.region,
            NEW.gateway,
            NEW.payment_method,
            1,
            1,
            NEW.amount,
            date_trunc('day', NEW.created_at),
            date_trunc('day', NEW.created_at) + interval '1 day'
        )
        ON CONFLICT (region, gateway, payment_method, period_start, period_end) 
        DO UPDATE SET
            total_transactions = regional_payment_metrics.total_transactions + 1,
            successful_transactions = regional_payment_metrics.successful_transactions + 1,
            total_revenue = regional_payment_metrics.total_revenue + EXCLUDED.total_revenue,
            conversion_rate = (regional_payment_metrics.successful_transactions + 1.0) / 
                            (regional_payment_metrics.total_transactions + 1.0);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for payment metrics
CREATE TRIGGER trigger_update_payment_metrics
    AFTER UPDATE ON payment_transactions
    FOR EACH ROW
    WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
    EXECUTE FUNCTION update_payment_metrics();


-- =====================================================
-- COMPLETADO
-- =====================================================

-- Verificar que todo se creó correctamente
SELECT 
    'Tables' as type, 
    COUNT(*) as count 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
UNION ALL
SELECT 
    'Views' as type, 
    COUNT(*) as count 
FROM information_schema.views 
WHERE table_schema = 'public'
UNION ALL
SELECT 
    'Functions' as type, 
    COUNT(*) as count 
FROM information_schema.routines 
WHERE routine_schema = 'public';
