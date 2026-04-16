# Multi-Region Ingestor - GitHub Actions Setup Guide

## 📋 Pre-requisitos

Antes de ejecutar el workflow de GitHub Actions, necesitas configurar los siguientes secrets:

## 🔑 Configurar Secrets en GitHub

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Secrets and variables** → **Actions**
3. Click en **New repository secret**
4. Añade los siguientes secrets:

### Secrets Obligatorios

| Secret Name | Descripción | Ejemplo |
|-------------|-------------|---------|
| `SUPABASE_URL` | URL de tu proyecto Supabase | `https://abcdefgh.supabase.co` |
| `SUPABASE_KEY` | Service role key de Supabase | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `RIOT_API_KEY` | API key de Riot Games Developer Portal | `RGAPI-12345678-abcd-...` |
| `STEAM_API_KEY` | API key de Steam Web API | `A1B2C3D4E5F6...` |

### Secrets Opcionales

| Secret Name | Descripción | Ejemplo |
|-------------|-------------|---------|
| `PROXY_URL` | URL de proxy rotativo para China | `http://user:pass@proxy.com:8080` |
| `WANPLUS_API_KEY` | API key de Wanplus (si existe) | `wanplus_123456...` |

## 📝 Obtener API Keys

### 1. Supabase Keys

1. Ve a tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Click en **Settings** → **API**
3. Copia:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** → `SUPABASE_KEY` ⚠️ (mantener secreto!)

### 2. Riot Games API Key

1. Crea cuenta en [Riot Developer Portal](https://developer.riotgames.com/)
2. Click en **REGISTER PRODUCT**
3. Completa el formulario:
   - **Product Name**: GameRadar AI
   - **Description**: E-sports scouting platform for Asian regions
   - **API Used**: League of Legends, TFT, Valorant
4. Genera **Production API Key**
5. Copia la key → `RIOT_API_KEY`

**Rate Limits:**
- Development Key: 20 requests/sec, 100 requests/2min
- Production Key: 3,000 requests/10min

### 3. Steam Web API Key

1. Ve a [Steam Web API Key Registration](https://steamcommunity.com/dev/apikey)
2. Log in con tu cuenta de Steam
3. Completa el formulario:
   - **Domain Name**: `gameradar.ai` (o tu dominio)
4. Copia la key → `STEAM_API_KEY`

**Rate Limits:**
- 100,000 calls/day
- No hay límite por segundo (pero recomendado max 10 req/sec)

### 4. Proxy URL (Opcional - Recomendado para China)

Para acceder a sitios chinos (Wanplus, ScoreGG), recomendamos usar un proxy:

**Opciones:**
- [Bright Data](https://brightdata.com/) - Residential IPs China
- [Oxylabs](https://oxylabs.io/) - Datacenter IPs China
- [Smartproxy](https://smartproxy.com/) - Rotating IPs

**Formato:**
```
http://username:password@proxy-server.com:port
```

**Ejemplo:**
```
http://customer-user123:pass456@gate.dc.smartproxy.com:20000
```

## 🧪 Verificar Setup

### Test 1: Ejecutar Schema SQL

1. Ve a Supabase Dashboard → SQL Editor
2. Copia el contenido de `ingestion_logs_schema.sql`
3. Click **Run**
4. Verificar que se crearon:
   - Tabla `ingestion_logs`
   - Vistas `v_ingestion_*`
   - Funciones `get_session_metrics()`, etc.

### Test 2: Manual Trigger del Workflow

1. Ve a GitHub → **Actions**
2. Selecciona workflow **Multi-Region Strategic Ingestor**
3. Click **Run workflow**
4. Configurar inputs:
   - **Regions**: `korea,india`
   - **Players per region**: `5`
   - **Enable fallback**: `true`
5. Click **Run workflow**

### Test 3: Verificar Logs en Supabase

Después de ejecutar el workflow:

```sql
-- Ver última sesión
SELECT * FROM v_ingestion_recent_sessions 
ORDER BY created_at DESC 
LIMIT 1;

-- Ver métricas globales
SELECT * FROM v_ingestion_global_metrics;

-- Health status
SELECT * FROM get_ingestion_health_status();
```

## 🚀 Ejecución Automática

Una vez configurados los secrets, el workflow se ejecuta automáticamente:

**Schedule:**
- 00:00 UTC (3am Argentina / 9am Vietnam / 9am Korea)
- 06:00 UTC (9am Argentina / 3pm Vietnam / 3pm Korea)
- 12:00 UTC (3pm Argentina / 9pm Vietnam / 9pm Korea)
- 18:00 UTC (9pm Argentina / 3am Vietnam+1 / 3am Korea+1)

**Regiones incluidas por defecto:**
- `china` (Wanplus → Riot KR → Loot.bet)
- `korea` (Riot KR → Dak.gg → OP.GG → Loot.bet)
- `india` (TEC India → Riot KR → Loot.bet)
- `vietnam` (Soha Game → Riot KR → OP.GG → Loot.bet)
- `japan` (Riot JP → Riot KR → Loot.bet)
- `sea` (Steam API → Riot SEA → Loot.bet)

**Players por región:**
- 10 players aleatorios de `players_to_ingest.json`

## 📊 Monitoreo

### GitHub Actions Artifacts

Cada ejecución genera:
- `ingestion-reports/ingestion_report_<session_id>.json`
- Retention: 30 días
- Último 10 artifacts conservados

### Supabase Logs

```sql
-- Ver últimas 10 sesiones
SELECT 
    session_id,
    start_time,
    total_players,
    successful,
    failed,
    success_rate,
    total_fallbacks
FROM v_ingestion_recent_sessions
ORDER BY start_time DESC
LIMIT 10;

-- Performance por fuente (últimos 7 días)
SELECT 
    source,
    total_requests,
    successful_requests,
    avg_success_rate,
    avg_duration_ms
FROM v_ingestion_source_metrics
WHERE last_request > NOW() - INTERVAL '7 days'
ORDER BY avg_success_rate DESC;

-- Tendencia diaria
SELECT * FROM v_ingestion_daily_trend
ORDER BY date DESC
LIMIT 7;
```

## 🛠️ Troubleshooting

### Error: "SUPABASE_URL is not set"

**Causa:** Secret no configurado correctamente

**Solución:**
1. Ve a Settings → Secrets → Actions
2. Verifica que `SUPABASE_URL` existe
3. El nombre debe ser EXACTAMENTE `SUPABASE_URL` (case-sensitive)

### Error: "Riot API rate limit exceeded"

**Causa:** Demasiados requests en poco tiempo

**Solución:**
1. Reducir `players_per_region` en el workflow (de 10 a 5)
2. Aumentar delays en `ingestion_config.json`:
   ```json
   {
     "rate_limit_delays": {
       "riot_api_kr": 2.0,
       "riot_api_jp": 2.0
     }
   }
   ```

### Error: "Wanplus: Connection timeout"

**Causa:** GFW bloqueando conexión directa a sitios chinos

**Solución:**
1. Configurar `PROXY_URL` secret con proxy en China
2. O desactivar Wanplus temporalmente:
   ```json
   {
     "active_regions": ["korea", "india", "vietnam", "japan", "sea"]
   }
   ```

### Workflow tarda más de 30 minutos

**Causa:** Timeouts en múltiples fuentes

**Solución:**
1. Reducir `max_concurrent_requests` (de 10 a 5)
2. Reducir `players_per_region` (de 10 a 5)
3. Activar cache agresivo:
   ```json
   {
     "enable_cache": true,
     "cache_ttl": 600
   }
   ```

## 💰 Costos Estimados

### GitHub Actions

**Free Tier:**
- 2,000 minutos/mes (repos públicos)
- 500 MB storage para artifacts

**Uso actual:**
- ~15 min por ejecución (6 regiones × 10 players)
- 4 ejecuciones/día = 60 min/día
- 30 días × 60 min = **1,800 min/mes**
- **Total: $0/mes** ✅ (dentro del free tier)

### API Calls

**Riot Games API:**
- Production Key: GRATIS
- Rate limit: 3,000 requests/10min
- Uso: ~240 requests/día (40 requests × 6 ejecuciones)
- **Total: $0/mes** ✅

**Steam Web API:**
- GRATIS
- Rate limit: 100,000 calls/día
- Uso: ~120 calls/día (20 SEA players × 6 ejecuciones)
- **Total: $0/mes** ✅

**Proxies (opcional):**
- Para Wanplus (China) recomendado
- Bright Data: ~$500/mes (50GB residential)
- Oxylabs: ~$300/mes (datacenter)
- **Solo si necesitas acceso a fuentes chinas**

## ✅ Checklist de Setup

- [ ] Ejecutar `ingestion_logs_schema.sql` en Supabase
- [ ] Configurar secret `SUPABASE_URL`
- [ ] Configurar secret `SUPABASE_KEY`
- [ ] Configurar secret `RIOT_API_KEY` (Riot Developer Portal)
- [ ] Configurar secret `STEAM_API_KEY` (Steam Web API)
- [ ] (Opcional) Configurar secret `PROXY_URL` para China
- [ ] Editar `players_to_ingest.example.json` → `players_to_ingest.json`
- [ ] Commit y push de archivos
- [ ] Manual trigger del workflow para test
- [ ] Verificar logs en Supabase con `SELECT * FROM v_ingestion_recent_sessions`
- [ ] Confirmar que los scheduled executions están funcionando

## 📚 Recursos

- [MULTI_REGION_INGESTOR.md](MULTI_REGION_INGESTOR.md) - Documentación completa
- [Riot Developer Portal](https://developer.riotgames.com/)
- [Steam Web API Documentation](https://steamcommunity.com/dev)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Supabase Docs](https://supabase.com/docs)
