-- ============================================================================
-- SCHEMA DE SEGURIDAD PARA STREET SCOUT
-- ============================================================================
-- Este script crea todas las tablas y políticas de seguridad necesarias
-- para implementar autenticación y autorización en GameRadar AI
-- ============================================================================

-- ============================================================================
-- 1. EXTENSIONES
-- ============================================================================

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 2. TABLAS DE SUSCRIPCIONES
-- ============================================================================

-- Tabla de planes disponibles
CREATE TABLE IF NOT EXISTS subscription_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(50) NOT NULL UNIQUE,
  slug VARCHAR(50) NOT NULL UNIQUE,
  price_usd DECIMAL(10, 2) NOT NULL,
  price_inr DECIMAL(10, 2),
  searches_per_month INTEGER NOT NULL,
  max_markets INTEGER NOT NULL,
  features JSONB NOT NULL,
  limits JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insertar planes
INSERT INTO subscription_plans (name, slug, price_usd, price_inr, searches_per_month, max_markets, features, limits) VALUES
  ('Street Scout', 'street-scout', 99.00, 7999.00, 50, 3, 
   '["3 Asian markets", "50 AI searches/month", "Basic analytics", "Email notifications", "Community support", "CSV export", "Weekly updates"]'::jsonb,
   '{"analytics_level": "basic", "api_access": false, "talent_ping": false}'::jsonb),
  ('Elite Analyst', 'elite-analyst', 299.00, 24999.00, -1, 7,
   '["All 7 Asian markets", "Unlimited searches", "Advanced analytics", "Real-time TalentPing", "Priority support", "API access", "Custom reports"]'::jsonb,
   '{"analytics_level": "advanced", "api_access": true, "talent_ping": true}'::jsonb),
  ('Organization', 'organization', 999.00, 79999.00, -1, 7,
   '["All markets", "Unlimited everything", "Multi-user accounts", "Dedicated support", "Custom integrations", "White-label options", "SLA guarantee"]'::jsonb,
   '{"analytics_level": "enterprise", "api_access": true, "talent_ping": true, "multi_user": true}'::jsonb);

-- Tabla de suscripciones de usuarios
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES subscription_plans(id),
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  -- Status: active, trial, paused, canceled, expired
  
  payment_gateway VARCHAR(20) NOT NULL,
  -- Gateway: stripe, razorpay, paypal
  
  gateway_subscription_id VARCHAR(255),
  gateway_customer_id VARCHAR(255),
  
  current_period_start TIMESTAMPTZ NOT NULL,
  current_period_end TIMESTAMPTZ NOT NULL,
  
  selected_markets TEXT[] DEFAULT ARRAY[]::TEXT[],
  -- Markets: ['kr', 'jp', 'th']
  
  trial_ends_at TIMESTAMPTZ,
  canceled_at TIMESTAMPTZ,
  
  metadata JSONB DEFAULT '{}'::jsonb,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT unique_active_subscription UNIQUE (user_id, status)
);

-- Índices para performance
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

-- Tabla de historial de pagos
CREATE TABLE IF NOT EXISTS payment_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) NOT NULL,
  
  payment_gateway VARCHAR(20) NOT NULL,
  gateway_payment_id VARCHAR(255) NOT NULL,
  gateway_status VARCHAR(50),
  
  payment_method VARCHAR(50),
  -- Method: card, upi, netbanking, paypal, etc.
  
  status VARCHAR(20) NOT NULL,
  -- Status: pending, succeeded, failed, refunded
  
  metadata JSONB DEFAULT '{}'::jsonb,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_history_subscription_id ON payment_history(subscription_id);
CREATE INDEX idx_payment_history_user_id ON payment_history(user_id);
CREATE INDEX idx_payment_history_status ON payment_history(status);

-- Tabla de uso de suscripción
CREATE TABLE IF NOT EXISTS subscription_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  
  searches_used INTEGER DEFAULT 0,
  searches_limit INTEGER NOT NULL,
  
  api_calls_used INTEGER DEFAULT 0,
  api_calls_limit INTEGER,
  
  last_search_at TIMESTAMPTZ,
  last_api_call_at TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT unique_subscription_period UNIQUE (subscription_id, period_start)
);

CREATE INDEX idx_subscription_usage_subscription_id ON subscription_usage(subscription_id);
CREATE INDEX idx_subscription_usage_period ON subscription_usage(period_start, period_end);

-- Tabla de búsquedas (para audit y analytics)
CREATE TABLE IF NOT EXISTS search_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  
  query TEXT NOT NULL,
  market VARCHAR(10),
  filters JSONB,
  
  results_count INTEGER DEFAULT 0,
  execution_time_ms INTEGER,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_search_logs_user_id ON search_logs(user_id);
CREATE INDEX idx_search_logs_created_at ON search_logs(created_at DESC);

-- ============================================================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLÍTICAS: subscription_plans
-- ============================================================================

-- Todos pueden leer los planes (página de pricing)
CREATE POLICY "Plans are viewable by everyone"
ON subscription_plans FOR SELECT
TO public
USING (true);

-- Solo admins pueden modificar planes
CREATE POLICY "Only admins can modify plans"
ON subscription_plans FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM auth.users
    WHERE auth.users.id = auth.uid()
    AND auth.users.role = 'service_role'
  )
);

-- ============================================================================
-- POLÍTICAS: subscriptions
-- ============================================================================

-- Usuarios solo pueden ver sus propias suscripciones
CREATE POLICY "Users can view own subscriptions"
ON subscriptions FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Solo el backend (service_role) puede crear suscripciones
CREATE POLICY "Service role can insert subscriptions"
ON subscriptions FOR INSERT
TO service_role
WITH CHECK (true);

-- Usuarios pueden actualizar ciertos campos de su suscripción
CREATE POLICY "Users can update own subscription fields"
ON subscriptions FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (
  auth.uid() = user_id 
  AND (
    -- Solo pueden cambiar selected_markets
    (OLD.selected_markets IS DISTINCT FROM NEW.selected_markets)
    OR (OLD.metadata IS DISTINCT FROM NEW.metadata)
  )
  AND OLD.status = NEW.status  -- No pueden cambiar status
  AND OLD.plan_id = NEW.plan_id  -- No pueden cambiar plan directamente
);

-- ============================================================================
-- POLÍTICAS: payment_history
-- ============================================================================

-- Usuarios solo pueden ver su historial de pagos
CREATE POLICY "Users can view own payment history"
ON payment_history FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Solo service role puede insertar pagos
CREATE POLICY "Service role can insert payments"
ON payment_history FOR INSERT
TO service_role
WITH CHECK (true);

-- ============================================================================
-- POLÍTICAS: subscription_usage
-- ============================================================================

-- Usuarios pueden ver su propio uso
CREATE POLICY "Users can view own usage"
ON subscription_usage FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Service role puede insertar/actualizar uso
CREATE POLICY "Service role can manage usage"
ON subscription_usage FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- POLÍTICAS: search_logs
-- ============================================================================

-- Usuarios pueden ver sus propias búsquedas
CREATE POLICY "Users can view own searches"
ON search_logs FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Usuarios pueden insertar sus búsquedas
CREATE POLICY "Users can insert own searches"
ON search_logs FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- 4. FUNCIONES HELPER
-- ============================================================================

-- Función para obtener suscripción activa del usuario
CREATE OR REPLACE FUNCTION get_active_subscription(p_user_id UUID)
RETURNS TABLE (
  subscription_id UUID,
  plan_name VARCHAR(50),
  plan_slug VARCHAR(50),
  status VARCHAR(20),
  searches_limit INTEGER,
  max_markets INTEGER,
  selected_markets TEXT[],
  current_period_end TIMESTAMPTZ
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    s.id,
    sp.name,
    sp.slug,
    s.status,
    sp.searches_per_month,
    sp.max_markets,
    s.selected_markets,
    s.current_period_end
  FROM subscriptions s
  JOIN subscription_plans sp ON s.plan_id = sp.id
  WHERE s.user_id = p_user_id
    AND s.status IN ('active', 'trial')
  ORDER BY s.created_at DESC
  LIMIT 1;
END;
$$;

-- Función para verificar si usuario puede hacer búsqueda
CREATE OR REPLACE FUNCTION can_user_search(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_subscription_id UUID;
  v_searches_used INTEGER;
  v_searches_limit INTEGER;
  v_status VARCHAR(20);
BEGIN
  -- Obtener suscripción activa
  SELECT s.id, s.status, sp.searches_per_month
  INTO v_subscription_id, v_status, v_searches_limit
  FROM subscriptions s
  JOIN subscription_plans sp ON s.plan_id = sp.id
  WHERE s.user_id = p_user_id
    AND s.status IN ('active', 'trial')
    AND s.current_period_end > NOW()
  LIMIT 1;
  
  -- No tiene suscripción activa
  IF v_subscription_id IS NULL THEN
    RETURN FALSE;
  END IF;
  
  -- Plan con búsquedas ilimitadas (-1)
  IF v_searches_limit = -1 THEN
    RETURN TRUE;
  END IF;
  
  -- Verificar uso en el período actual
  SELECT COALESCE(su.searches_used, 0)
  INTO v_searches_used
  FROM subscription_usage su
  WHERE su.subscription_id = v_subscription_id
    AND su.period_start <= NOW()
    AND su.period_end > NOW()
  LIMIT 1;
  
  -- Tiene búsquedas disponibles
  RETURN v_searches_used < v_searches_limit;
END;
$$;

-- Función para incrementar contador de búsquedas
CREATE OR REPLACE FUNCTION increment_search_count(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_subscription_id UUID;
  v_usage_id UUID;
BEGIN
  -- Obtener suscripción activa
  SELECT id INTO v_subscription_id
  FROM subscriptions
  WHERE user_id = p_user_id
    AND status IN ('active', 'trial')
    AND current_period_end > NOW()
  LIMIT 1;
  
  IF v_subscription_id IS NULL THEN
    RETURN FALSE;
  END IF;
  
  -- Buscar o crear registro de uso para el período actual
  INSERT INTO subscription_usage (
    subscription_id,
    user_id,
    period_start,
    period_end,
    searches_used,
    searches_limit,
    last_search_at
  )
  SELECT 
    v_subscription_id,
    p_user_id,
    s.current_period_start,
    s.current_period_end,
    1,
    sp.searches_per_month,
    NOW()
  FROM subscriptions s
  JOIN subscription_plans sp ON s.plan_id = sp.id
  WHERE s.id = v_subscription_id
  ON CONFLICT (subscription_id, period_start) 
  DO UPDATE SET
    searches_used = subscription_usage.searches_used + 1,
    last_search_at = NOW(),
    updated_at = NOW();
  
  RETURN TRUE;
END;
$$;

-- Función para renovar suscripción (llamada por webhook de pago)
CREATE OR REPLACE FUNCTION renew_subscription(
  p_subscription_id UUID,
  p_payment_id VARCHAR(255),
  p_amount DECIMAL(10, 2),
  p_currency VARCHAR(3),
  p_gateway VARCHAR(20)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_user_id UUID;
  v_new_period_end TIMESTAMPTZ;
BEGIN
  -- Obtener user_id y calcular nueva fecha
  SELECT user_id, current_period_end + INTERVAL '1 month'
  INTO v_user_id, v_new_period_end
  FROM subscriptions
  WHERE id = p_subscription_id;
  
  IF v_user_id IS NULL THEN
    RETURN FALSE;
  END IF;
  
  -- Actualizar suscripción
  UPDATE subscriptions
  SET 
    current_period_start = current_period_end,
    current_period_end = v_new_period_end,
    status = 'active',
    updated_at = NOW()
  WHERE id = p_subscription_id;
  
  -- Registrar pago
  INSERT INTO payment_history (
    subscription_id,
    user_id,
    amount,
    currency,
    payment_gateway,
    gateway_payment_id,
    status
  ) VALUES (
    p_subscription_id,
    v_user_id,
    p_amount,
    p_currency,
    p_gateway,
    p_payment_id,
    'succeeded'
  );
  
  RETURN TRUE;
END;
$$;

-- ============================================================================
-- 5. TRIGGERS
-- ============================================================================

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_history_updated_at BEFORE UPDATE ON payment_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscription_usage_updated_at BEFORE UPDATE ON subscription_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. VISTAS (VIEWS)
-- ============================================================================

-- Vista de suscripciones activas con detalles
CREATE OR REPLACE VIEW active_subscriptions_view AS
SELECT 
  s.id AS subscription_id,
  s.user_id,
  u.email,
  sp.name AS plan_name,
  sp.slug AS plan_slug,
  sp.price_usd,
  s.status,
  s.current_period_start,
  s.current_period_end,
  s.selected_markets,
  sp.searches_per_month AS searches_limit,
  COALESCE(su.searches_used, 0) AS searches_used,
  sp.max_markets,
  s.created_at AS subscription_created_at
FROM subscriptions s
JOIN subscription_plans sp ON s.plan_id = sp.id
JOIN auth.users u ON s.user_id = u.id
LEFT JOIN subscription_usage su ON
  su.subscription_id = s.id
  AND su.period_start <= NOW()
  AND su.period_end > NOW()
WHERE s.status IN ('active', 'trial')
  AND s.current_period_end > NOW();

-- ============================================================================
-- 7. ÍNDICES ADICIONALES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status) WHERE status IN ('active', 'trial');
CREATE INDEX idx_subscriptions_period ON subscriptions(current_period_start, current_period_end);
CREATE INDEX idx_search_logs_user_created ON search_logs(user_id, created_at DESC);

-- ============================================================================
-- 8. COMENTARIOS PARA DOCUMENTACIÓN
-- ============================================================================

COMMENT ON TABLE subscription_plans IS 'Planes de suscripción disponibles (Street Scout, Elite Analyst, Organization)';
COMMENT ON TABLE subscriptions IS 'Suscripciones activas de usuarios con información de pago';
COMMENT ON TABLE payment_history IS 'Historial completo de transacciones de pago';
COMMENT ON TABLE subscription_usage IS 'Tracking de uso mensual por suscripción';
COMMENT ON TABLE search_logs IS 'Log de todas las búsquedas realizadas para analytics';

COMMENT ON FUNCTION can_user_search IS 'Verifica si un usuario tiene búsquedas disponibles en su plan';
COMMENT ON FUNCTION increment_search_count IS 'Incrementa el contador de búsquedas del usuario';
COMMENT ON FUNCTION renew_subscription IS 'Renueva una suscripción después de un pago exitoso';

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================

-- Para ejecutar este script en Supabase:
-- 1. Ve a SQL Editor en tu dashboard de Supabase
-- 2. Crea una nueva query
-- 3. Pega este script completo
-- 4. Ejecuta (Run)
-- 5. Verifica que todas las tablas se crearon correctamente
