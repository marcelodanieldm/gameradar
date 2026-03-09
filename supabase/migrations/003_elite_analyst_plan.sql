-- Migration: Elite Analyst Plan and New Features
-- Description: Adds Elite Analyst subscription plan and related features (TalentPing alerts, API access)

-- =====================================================
-- 1. ADD ELITE ANALYST PLAN
-- =====================================================

-- Insert Elite Analyst subscription plan
INSERT INTO subscription_plans (name, price, search_limit, markets_limit, features, description)
VALUES (
  'Elite Analyst',
  299.00,
  999999, -- Unlimited (represented as very high number)
  7, -- All 7 markets
  ARRAY[
    'all_7_markets',
    'unlimited_searches',
    'advanced_analytics',
    'ai_insights',
    'talent_ping_alerts',
    'api_access',
    'priority_support',
    'custom_reports',
    'real_time_notifications',
    'webhook_integration'
  ],
  'Professional team access with unlimited searches, advanced analytics, and real-time alerts'
)
ON CONFLICT (name) DO UPDATE SET
  price = EXCLUDED.price,
  search_limit = EXCLUDED.search_limit,
  markets_limit = EXCLUDED.markets_limit,
  features = EXCLUDED.features,
  description = EXCLUDED.description;

-- =====================================================
-- 2. TALENT PING ALERTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS talent_ping_alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  markets TEXT[] NOT NULL DEFAULT '{}',
  games TEXT[] NOT NULL DEFAULT '{}',
  criteria JSONB NOT NULL DEFAULT '{}',
  notification_channels TEXT[] NOT NULL DEFAULT ARRAY['email'],
  is_active BOOLEAN NOT NULL DEFAULT true,
  matches_found INTEGER NOT NULL DEFAULT 0,
  last_triggered TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_talent_ping_alerts_user_id ON talent_ping_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_talent_ping_alerts_is_active ON talent_ping_alerts(is_active);

-- Row Level Security
ALTER TABLE talent_ping_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own alerts" ON talent_ping_alerts
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own alerts" ON talent_ping_alerts
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own alerts" ON talent_ping_alerts
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own alerts" ON talent_ping_alerts
  FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- 3. API KEYS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  key VARCHAR(255) NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  requests_today INTEGER NOT NULL DEFAULT 0,
  requests_total INTEGER NOT NULL DEFAULT 0,
  last_used TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own API keys" ON api_keys
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own API keys" ON api_keys
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own API keys" ON api_keys
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own API keys" ON api_keys
  FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- 4. API USAGE LOGS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS api_usage_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  endpoint VARCHAR(255) NOT NULL,
  method VARCHAR(10) NOT NULL,
  status_code INTEGER NOT NULL,
  response_time_ms INTEGER,
  request_body JSONB,
  response_body JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_user_id ON api_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_api_key_id ON api_usage_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_created_at ON api_usage_logs(created_at);

-- Row Level Security
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own API usage" ON api_usage_logs
  FOR SELECT USING (auth.uid() = user_id);

-- =====================================================
-- 5. ALERT MATCHES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS alert_matches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  alert_id UUID NOT NULL REFERENCES talent_ping_alerts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  player_data JSONB NOT NULL,
  match_score FLOAT NOT NULL DEFAULT 0,
  notification_sent BOOLEAN NOT NULL DEFAULT false,
  notification_sent_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_alert_matches_alert_id ON alert_matches(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_matches_user_id ON alert_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_matches_created_at ON alert_matches(created_at);

-- Row Level Security
ALTER TABLE alert_matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own alert matches" ON alert_matches
  FOR SELECT USING (auth.uid() = user_id);

-- =====================================================
-- 6. UPDATE SUBSCRIPTION USAGE FOR UNLIMITED
-- =====================================================

-- Function to check if user has unlimited searches (Elite Analyst plan)
CREATE OR REPLACE FUNCTION has_unlimited_searches(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  v_plan_name VARCHAR(100);
BEGIN
  SELECT sp.name INTO v_plan_name
  FROM subscriptions s
  JOIN subscription_plans sp ON s.plan_id = sp.id
  WHERE s.user_id = p_user_id
    AND s.status = 'active'
    AND s.current_period_end > NOW()
  LIMIT 1;
  
  RETURN v_plan_name = 'Elite Analyst';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update can_user_search to handle unlimited searches
CREATE OR REPLACE FUNCTION can_user_search(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  v_searches_count INTEGER;
  v_search_limit INTEGER;
  v_is_unlimited BOOLEAN;
BEGIN
  -- Check if user has unlimited searches
  SELECT has_unlimited_searches(p_user_id) INTO v_is_unlimited;
  
  IF v_is_unlimited THEN
    RETURN TRUE;
  END IF;
  
  -- Otherwise check normal limits
  SELECT 
    COALESCE(su.searches_count, 0),
    sp.search_limit
  INTO v_searches_count, v_search_limit
  FROM subscriptions s
  JOIN subscription_plans sp ON s.plan_id = sp.id
  LEFT JOIN subscription_usage su ON su.user_id = s.user_id
  WHERE s.user_id = p_user_id
    AND s.status = 'active'
    AND s.current_period_end > NOW()
  LIMIT 1;
  
  RETURN v_searches_count < v_search_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 7. ADD ELITE ANALYST STATS VIEW
-- =====================================================

CREATE OR REPLACE VIEW elite_analyst_stats AS
SELECT 
  s.user_id,
  sp.name as plan_name,
  COALESCE(su.searches_count, 0) as searches_count,
  sp.search_limit,
  s.current_period_start,
  s.current_period_end,
  s.selected_markets,
  COUNT(DISTINCT tpa.id) FILTER (WHERE tpa.is_active = true) as active_alerts,
  COUNT(DISTINCT ak.id) FILTER (WHERE ak.is_active = true) as active_api_keys,
  COALESCE(SUM(ak.requests_today), 0) as api_calls_today,
  su.last_search_at
FROM subscriptions s
JOIN subscription_plans sp ON s.plan_id = sp.id
LEFT JOIN subscription_usage su ON su.user_id = s.user_id
LEFT JOIN talent_ping_alerts tpa ON tpa.user_id = s.user_id
LEFT JOIN api_keys ak ON ak.user_id = s.user_id
WHERE s.status = 'active'
  AND s.current_period_end > NOW()
  AND sp.name = 'Elite Analyst'
GROUP BY s.user_id, sp.name, su.searches_count, sp.search_limit, 
         s.current_period_start, s.current_period_end, s.selected_markets, su.last_search_at;

-- =====================================================
-- 8. FUNCTION TO RESET DAILY API COUNTS
-- =====================================================

CREATE OR REPLACE FUNCTION reset_daily_api_counts()
RETURNS void AS $$
BEGIN
  UPDATE api_keys
  SET requests_today = 0
  WHERE requests_today > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 9. FUNCTION TO LOG API USAGE
-- =====================================================

CREATE OR REPLACE FUNCTION log_api_usage(
  p_user_id UUID,
  p_api_key_id UUID,
  p_endpoint VARCHAR(255),
  p_method VARCHAR(10),
  p_status_code INTEGER,
  p_response_time_ms INTEGER DEFAULT NULL,
  p_ip_address INET DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
  -- Insert usage log
  INSERT INTO api_usage_logs (
    user_id,
    api_key_id,
    endpoint,
    method,
    status_code,
    response_time_ms,
    ip_address,
    user_agent
  ) VALUES (
    p_user_id,
    p_api_key_id,
    p_endpoint,
    p_method,
    p_status_code,
    p_response_time_ms,
    p_ip_address,
    p_user_agent
  );
  
  -- Update API key stats
  UPDATE api_keys
  SET 
    requests_today = requests_today + 1,
    requests_total = requests_total + 1,
    last_used = NOW()
  WHERE id = p_api_key_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 10. GRANTS
-- =====================================================

GRANT SELECT ON elite_analyst_stats TO authenticated;
GRANT EXECUTE ON FUNCTION has_unlimited_searches(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION log_api_usage(UUID, UUID, VARCHAR, VARCHAR, INTEGER, INTEGER, INET, TEXT) TO authenticated;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Summary:
-- ✓ Elite Analyst plan added with $299/month pricing
-- ✓ TalentPing alerts table with RLS
-- ✓ API keys table with RLS
-- ✓ API usage logging system
-- ✓ Alert matches tracking
-- ✓ Unlimited searches support
-- ✓ Elite analyst stats view
-- ✓ Daily API count reset function
