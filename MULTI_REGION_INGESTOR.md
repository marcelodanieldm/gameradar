# 🌍 Multi-Region Strategic Ingestor - Documentación Completa

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Fuentes de Datos](#fuentes-de-datos)
4. [Configuración](#configuración)
5. [Uso](#uso)
6. [Fallback System](#fallback-system)
7. [GitHub Actions](#github-actions)
8. [Monitoring y Logs](#monitoring-y-logs)
9. [Troubleshooting](#troubleshooting)
10. [Extensibilidad](#extensibilidad)

---

## 🎯 Visión General

El **Multi-Region Strategic Ingestor** es un sistema de **grado militar** diseñado para:

- ✅ Ingerir datos desde **7+ fuentes estratégicas** simultáneamente
- ✅ **Fallback automático** entre fuentes (resistencia a fallos)
- ✅ **Segmentación regional** con prioridades específicas:
  - **Micro-metrics** (Korea/China): APM, Gold/Min, DMG%
  - **Social Sentiment** (India/Vietnam): Consistency, Community Rating
- ✅ **Logging detallado** a Supabase para analytics
- ✅ **Ejecución serverless** vía GitHub Actions (costo $0)
- ✅ **Anti-detection** avanzado por región
- ✅ **Circuit Breaker** para evitar bombardear fuentes caídas

---

## 🏛️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│               MultiRegionIngestor                           │
│  (Orquestador de Grado Militar)                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌──────────────────────┐
│ UniversalAgg    │   │ StrategicAdapters    │
│ (Existing)      │   │ (New)                │
│                 │   │                      │
│ - OP.GG         │   │ - Wanplus (China)    │
│ - Dak.gg        │   │ - TEC India          │
│ - Riot API      │   │ - Soha Game (VN)     │
│                 │   │ - Steam API (SEA)    │
│                 │   │ - Loot.bet (Odds)    │
│                 │   │ - Riot Shards (JP/KR)│
└─────────────────┘   └──────────────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │   Fallback System     │
        │   (Cascade/Smart)     │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Supabase Bronze      │
        │  + Ingestion Logs     │
        └───────────────────────┘
```

### Componentes Principales

| Componente | Responsabilidad |
|------------|-----------------|
| **MultiRegionIngestor** | Orquestación, concurrencia, fallback, logging |
| **StrategicAdapters** | Adapters especializados por fuente |
| **UniversalAggregator** | Adapters existentes (OP.GG, Dak.gg, etc) |
| **FallbackStrategy** | Define cadenas de fallback por región |
| **AdvancedHeaderRotator** | Anti-detection con headers regionales |
| **CircuitBreaker** | Evita bombardear fuentes caídas |
| **SimpleCache** | Reduce requests duplicados |

---

## 🌐 Fuentes de Datos

### China Deep-Links

#### 1. **Wanplus.com** (LPL/KPL)
- **Prioridad**: MICRO_METRICS
- **Datos clave**: APM, Gold/Min, DMG%, Win Rate, KDA
- **Requiere proxy**: ✅ Sí (Great Firewall)
- **Rate limit**: 20 req/min
- **Reliability**: 85%

**Ejemplo de datos extraídos:**
```json
{
  "nickname": "JackeyLove",
  "apm": 285,
  "gold_per_min": 425,
  "damage_percent": 32.5,
  "win_rate": 68.5,
  "kda": 5.2
}
```

#### 2. **ScoreGG** (已集成在 RegionalConnectors)
- Ver documentación: [REGIONAL_CONNECTORS.md](REGIONAL_CONNECTORS.md)

---

### India/SEA Mobile

#### 3. **The Esports Club** (India)
- **Prioridad**: SOCIAL_SENTIMENT
- **Datos clave**: Consistency Score, Community Rating, Tournament Participations
- **Requiere proxy**: ❌ No
- **Rate limit**: 40 req/min
- **Reliability**: 75%

**Ejemplo de datos extraídos:**
```json
{
  "nickname": "IndianPro123",
  "consistency_score": 75,
  "community_rating": 4.5,
  "tournament_participations": 12,
  "win_rate": 58.0
}
```

#### 4. **Soha Game Network** (Vietnam)
- **Prioridad**: SOCIAL_SENTIMENT
- **Datos clave**: VCS/VPL stats, social metrics
- **Requiere proxy**: ❌ No
- **Rate limit**: 30 req/min
- **Reliability**: 70%

---

### Global APIs

#### 5. **Steam Web API** (Dota 2 SEA)
- **Prioridad**: MICRO_METRICS
- **Datos clave**: MMR, GPM, XPM, KDA, Hero stats
- **Requiere API key**: ✅ Sí
- **Rate limit**: 100 req/min
- **Reliability**: 95%

**Setup:**
```bash
# Obtener Steam API key
# https://steamcommunity.com/dev/apikey

# Agregar a .env
STEAM_API_KEY=your_steam_key_here
```

#### 6. **Riot Games Shards** (JP/KR)
- **Prioridad**: MICRO_METRICS
- **Datos clave**: Ranked stats oficiales, match history
- **Requiere API key**: ✅ Sí
- **Rate limit**: 100 req/min
- **Reliability**: 98% (fuente oficial)

**Setup:**
```bash
# Obtener Riot API key
# https://developer.riotgames.com/

# Agregar a .env
RIOT_API_KEY=your_riot_key_here
```

#### 7. **Loot.bet** (Betting Odds Proxy)
- **Prioridad**: MICRO_METRICS
- **Datos clave**: Performance score basado en odds
- **Requiere proxy**: ❌ No
- **Rate limit**: 30 req/min
- **Reliability**: 80%

**Lógica:**
- Odds bajas (1.5) = Performance score ~95
- Odds altas (3.0) = Performance score ~60

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crear archivo `.env`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# API Keys
RIOT_API_KEY=your-riot-key
STEAM_API_KEY=your-steam-key

# Proxies (opcional para China)
CHINA_PROXY_URL=http://proxy.example.com:8080
CHINA_PROXY_USER=username
CHINA_PROXY_PASS=password
```

### 2. Configuración de Ingesta

Copiar `ingestion_config.example.json` a `ingestion_config.json`:

```json
{
  "max_concurrent_requests": 10,
  "max_concurrent_per_source": 3,
  "enable_fallback": true,
  "fallback_strategy": "cascade",
  "cache_ttl": 300,
  "circuit_breaker_threshold": 5,
  "log_to_supabase": true,
  "log_level": "INFO"
}
```

**Parámetros clave:**

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `max_concurrent_requests` | Máximo requests simultáneos | 10 |
| `max_concurrent_per_source` | Máximo por fuente | 3 |
| `enable_fallback` | Activar fallback automático | true |
| `fallback_strategy` | `cascade`, `parallel`, `smart` | cascade |
| `cache_ttl` | TTL del cache en segundos | 300 |
| `circuit_breaker_threshold` | Fallos antes de abrir circuit | 5 |
| `log_to_supabase` | Guardar logs en DB | true |

### 3. Lista de Jugadores

Copiar `players_to_ingest.example.json` a `players_to_ingest.json`:

```json
{
  "china": ["JackeyLove", "TheShy", "Ming"],
  "korea": ["Faker", "ShowMaker", "Chovy"],
  "india": ["IndianPro1", "IndianPro2"],
  "vietnam": ["Levi", "SofM"],
  "japan": ["Evi", "Yutapon"],
  "sea": ["SEAPro1", "SEAPro2"]
}
```

### 4. Setup de Supabase

Ejecutar `ingestion_logs_schema.sql` en Supabase SQL Editor:

```bash
# 1. Abrir Supabase Dashboard
# 2. SQL Editor
# 3. Copiar contenido de ingestion_logs_schema.sql
# 4. Run
```

Esto creará:
- ✅ Tabla `ingestion_logs`
- ✅ Vistas analíticas (`v_ingestion_global_metrics`, etc)
- ✅ Funciones helper (`get_session_metrics`, `get_ingestion_health_status`)

---

## 🚀 Uso

### Modo 1: Desarrollo Local

```python
import asyncio
from MultiRegionIngestor import MultiRegionIngestor, IngestionConfig, RegionProfile

async def main():
    # Setup config
    config = IngestionConfig(
        max_concurrent_requests=10,
        enable_fallback=True,
        log_to_supabase=True
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        # Opción A: Single player
        result = await ingestor.ingest_player(
            "Faker",
            region=RegionProfile.KOREA,
            game="lol"
        )
        
        if result.success:
            print(f"✅ Success: {result.data['nickname']}")
        else:
            print(f"❌ Failed: {result.error}")
        
        # Opción B: Batch
        korean_players = [
            ("Faker", RegionProfile.KOREA),
            ("ShowMaker", RegionProfile.KOREA),
            ("Chovy", RegionProfile.KOREA),
        ]
        
        report = await ingestor.ingest_players_batch(
            korean_players,
            game="lol"
        )
        
        print(f"Success Rate: {report.success_rate:.2f}%")
        print(f"Duration: {report.duration_seconds:.2f}s")
        
        # Opción C: Region-priority
        players_by_region = {
            RegionProfile.KOREA: ["Faker", "Chovy"],
            RegionProfile.CHINA: ["JackeyLove", "TheShy"],
            RegionProfile.INDIA: ["IndianPro1", "IndianPro2"]
        }
        
        reports = await ingestor.ingest_by_region_priority(
            players_by_region,
            game="lol"
        )
        
        for region, region_report in reports.items():
            print(f"{region}: {region_report.success_rate:.2f}%")

asyncio.run(main())
```

### Modo 2: GitHub Actions (Serverless)

**Ejecución automática cada 6 horas:**

```yaml
# .github/workflows/multi_region_ingestion.yml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

**Ejecución manual:**

1. Ir a GitHub → Actions
2. Seleccionar "Multi-Region Strategic Ingestion"
3. Click "Run workflow"
4. Configurar inputs:
   - **regions**: `china,korea,india,vietnam`
   - **players_per_region**: `50`
   - **enable_fallback**: `true`
5. Run!

**Resultados:**
- Artifacts descargables con reportes JSON
- Summary en la página del workflow
- Logs en Supabase (`ingestion_logs` table)

### Modo 3: Función de Conveniencia

```python
from MultiRegionIngestor import run_scheduled_ingestion
import asyncio

# Leer config y players desde archivos JSON
asyncio.run(run_scheduled_ingestion(
    config_file="ingestion_config.json",
    players_file="players_to_ingest.json"
))
```

---

## 🔄 Fallback System

### Cadenas de Fallback por Región

El sistema define cadenas de fallback inteligentes basadas en la región:

#### China
```
Primary: Wanplus → Riot API KR → Loot.bet
```

#### Korea
```
Primary: Riot API KR → Dak.gg → OP.GG → Loot.bet
```

#### Japan
```
Primary: Riot API JP → OP.GG → Loot.bet
```

#### India
```
Primary: TEC India → Riot API KR → Loot.bet
```

#### Vietnam
```
Primary: Soha Game → OP.GG → Loot.bet
```

#### SEA (Dota 2)
```
Primary: Steam API → OP.GG (LoL) → Loot.bet
```

### Ejemplo de Fallback en Acción

```python
# Configuración
player = "Faker"
region = RegionProfile.KOREA
sources = ["riot_api_kr", "dakgg", "opgg", "loot_bet"]

# Ejecución:
# 1. Intenta Riot API KR
#    → ❌ Error 401 (API key inválida)
#
# 2. Fallback → Dak.gg
#    → ❌ Timeout (30s)
#
# 3. Fallback → OP.GG
#    → ✅ Success! 
#
# Resultado:
# - Data obtenida de OP.GG
# - Fallback usado: True
# - Fallback source: opgg
# - Total fallbacks en sesión: +1
```

### Estrategias de Fallback

#### 1. **Cascade** (Default)
Intenta fuentes en secuencia hasta encontrar datos:
```
Source 1 → (fail) → Source 2 → (fail) → Source 3 → (success)
```

#### 2. **Parallel** (Futuro)
Intenta todas las fuentes en paralelo, devuelve la primera que responda:
```
Source 1 ┐
Source 2 ├─→ (primer resultado válido)
Source 3 ┘
```

#### 3. **Smart** (Futuro)
Usa machine learning para predecir cuál fuente tiene más probabilidad de éxito.

---

## ⚡ GitHub Actions - Guía Completa

### Setup Inicial

#### 1. Configurar Secrets

GitHub → Settings → Secrets and variables → Actions:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...your-key
RIOT_API_KEY=RGAPI-...
STEAM_API_KEY=...
```

#### 2. Workflow File

El workflow ya está en `.github/workflows/multi_region_ingestion.yml`

#### 3. Personalizar Players List

Editar directamente en el workflow o crear `players_to_ingest.json` en el repo.

### Ejecución y Monitoreo

#### Ver Logs en Tiempo Real

1. GitHub → Actions
2. Click en el workflow en ejecución
3. Expandir "Run Multi-Region Ingestion"
4. Ver logs en tiempo real

#### Descargar Reportes

1. Workflow completado → Artifacts
2. Download `ingestion-reports-{run_number}`
3. Contiene:
   - `ingestion_report_china_*.json`
   - `ingestion_report_korea_*.json`
   - `multi_region_ingestor_*.log`

#### Ver Summary

El workflow genera un summary automático:

```markdown
## 📊 Ingestion Reports

### 📄 ingestion_report_korea_abc123.json
- **Total Players:** 15
- **Successful:** 14
- **Failed:** 1
- **Success Rate:** 93.33%
- **Duration:** 45.2s

### 📄 ingestion_report_china_abc123.json
- **Total Players:** 10
- **Successful:** 8
- **Failed:** 2
- **Success Rate:** 80.00%
- **Duration:** 67.8s
```

### Costos

**Estimado:** $0/mes

- GitHub Actions: 2,000 minutos gratis/mes
- Ejecución promedio: 2-5 minutos
- Frecuencia: 4 veces/día = 120 ejecuciones/mes
- Total: ~600 minutos/mes < 2,000 ✅

**Optimizaciones:**
- Timeout máximo: 30 minutos (evitar runaway costs)
- Cleanup automático de artifacts viejos
- Caché de dependencias Python

---

## 📊 Monitoring y Logs

### 1. Logs en Supabase

Consultar logs desde Supabase SQL Editor:

```sql
-- Métricas globales
SELECT * FROM v_ingestion_global_metrics;

-- Performance por fuente
SELECT * FROM v_ingestion_source_metrics
ORDER BY total_requests DESC;

-- Tendencia diaria
SELECT * FROM v_ingestion_daily_trend
WHERE ingestion_date > CURRENT_DATE - INTERVAL '7 days';

-- Últimas 10 sesiones
SELECT * FROM v_ingestion_recent_sessions;

-- Health check
SELECT * FROM get_ingestion_health_status();
```

### 2. Logs Locales

Archivos generados automáticamente:

```
multi_region_ingestor_{timestamp}.log
```

Formato:
```
2026-04-16 10:30:45 | INFO | 🚀 Starting batch ingestion: 15 players
2026-04-16 10:30:47 | INFO | 🎯 Ingesting player: Faker (region: korea)
2026-04-16 10:30:49 | SUCCESS | ✅ Fetched Faker from riot_api_kr
2026-04-16 10:30:50 | INFO | 📦 Inserted to Bronze: Faker
```

### 3. Métricas por Adapter

```python
async with MultiRegionIngestor(config) as ingestor:
    # ... ejecutar ingesta ...
    
    # Obtener métricas de un adapter
    wanplus_metrics = ingestor.adapters["wanplus"].get_metrics()
    
    print(wanplus_metrics)
    # {
    #   "source": "wanplus",
    #   "requests": 10,
    #   "successes": 8,
    #   "failures": 2,
    #   "success_rate": 80.0,
    #   "avg_delay": 4.5
    # }
```

### 4. Alerts y Notificaciones

**Configurar notificaciones en GitHub Actions:**

```yaml
- name: 🔔 Notify on Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Multi-region ingestion failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**O usar Discord:**

```yaml
- name: 🔔 Discord Notification
  if: failure()
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK }} \
      -H "Content-Type: application/json" \
      -d '{"content": "❌ Ingestion failed!"}'
```

---

## 🐛 Troubleshooting

### Problema 1: API Key Inválida

**Síntoma:**
```
❌ Error fetching Faker: 401 Unauthorized
```

**Solución:**
1. Verificar que la API key esté en `.env`:
   ```bash
   echo $RIOT_API_KEY
   ```
2. Verificar que la key no haya expirado
3. Regenerar en [developer.riotgames.com](https://developer.riotgames.com/)

---

### Problema 2: Circuit Breaker Siempre Abierto

**Síntoma:**
```
⚡ Circuit breaker open for wanplus, skipping...
```

**Solución:**
1. Verificar si la fuente está realmente caída:
   ```bash
   curl -I https://www.wanplus.com
   ```
2. Aumentar threshold:
   ```json
   {
     "circuit_breaker_threshold": 10
   }
   ```
3. Resetear circuit manualmente:
   ```python
   ingestor.circuit_breaker.circuits["wanplus"]["failures"] = 0
   ```

---

### Problema 3: Timeouts en China

**Síntoma:**
```
❌ Error fetching JackeyLove: Timeout (30s)
```

**Solución:**
1. Verificar proxy:
   ```bash
   curl -x $CHINA_PROXY_URL https://www.wanplus.com
   ```
2. Aumentar timeout:
   ```json
   {
     "request_timeout": 60
   }
   ```
3. Usar proxy premium (BrightData, Smartproxy)

---

### Problema 4: Rate Limit Exceeded

**Síntoma:**
```
❌ Error: 429 Too Many Requests
```

**Solución:**
1. Reducir concurrencia:
   ```json
   {
     "max_concurrent_requests": 5,
     "max_concurrent_per_source": 2
   }
   ```
2. Aumentar delays en `ExponentialBackoffHandler`
3. Activar cache para reducir requests duplicados

---

### Problema 5: Todos los Adapters Fallan

**Síntoma:**
```
❌ Failed to ingest Faker from all sources
```

**Checklist:**
1. ✅ Internet conectado?
   ```bash
   ping www.google.com
   ```
2. ✅ Supabase accesible?
   ```bash
   curl $SUPABASE_URL
   ```
3. ✅ API keys configuradas?
   ```bash
   env | grep API_KEY
   ```
4. ✅ Fuentes no bloqueadas?
   ```bash
   curl -I https://www.op.gg
   ```

---

## 🔧 Extensibilidad

### Agregar Nueva Fuente

#### Paso 1: Crear Adapter

```python
# En StrategicAdapters.py

class MyNewSourceAdapter(BaseStrategicAdapter):
    """Adapter para mi nueva fuente"""
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        metadata = SourceMetadata(
            source_name="my_new_source",
            region=RegionProfile.GLOBAL,
            priority=DataPriority.MICRO_METRICS,
            base_url="https://mynewsource.com",
            requires_proxy=False,
            rate_limit_per_minute=50,
            reliability_score=0.90
        )
        super().__init__(client, metadata)
    
    async def fetch_player(self, identifier, game="lol", **kwargs):
        # Implementar fetch
        pass
    
    def _normalize_to_bronze_schema(self, raw_data):
        # Normalizar a esquema Bronze
        return {
            "nickname": raw_data.get("nickname"),
            "game": "LOL",
            # ...
        }
```

#### Paso 2: Registrar en Factory

```python
# En StrategicAdapters.py - StrategicAdapterFactory

_adapters: Dict[str, type] = {
    # ...existing adapters...
    "my_new_source": MyNewSourceAdapter,
}
```

#### Paso 3: Agregar a Fallback Chain

```python
# En MultiRegionIngestor.py - FallbackStrategy

FALLBACK_CHAINS = {
    RegionProfile.GLOBAL: [
        "riot_api_kr",
        "opgg",
        "my_new_source",  # <-- Agregar aquí
        "loot_bet"
    ]
}
```

#### Paso 4: Inicializar en MultiRegionIngestor

```python
# En MultiRegionIngestor._initialize_adapters()

self.adapters["my_new_source"] = MyNewSourceAdapter(client=self.client)
```

#### Paso 5: Usar!

```python
result = await ingestor.ingest_player(
    "PlayerName",
    region=RegionProfile.GLOBAL,
    preferred_sources=["my_new_source"]
)
```

---

### Agregar Nueva Región

```python
# En StrategicAdapters.py

class RegionProfile(str, Enum):
    # ... existing ...
    BRAZIL = "brazil"

# En AdvancedHeaderRotator

REGIONAL_USER_AGENTS = {
    # ... existing ...
    RegionProfile.BRAZIL: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    ]
}

REGIONAL_LANGUAGES = {
    # ... existing ...
    RegionProfile.BRAZIL: "pt-BR,pt;q=0.9,en;q=0.8"
}
```

---

## 📚 Referencias

- [UniversalAggregator.md](UNIVERSAL_AGGREGATOR.md) - Sistema de agregación existente
- [RegionalConnectors.md](REGIONAL_CONNECTORS.md) - Conectores regionales (Dak.gg, ScoreGG)
- [httpx Documentation](https://www.python-httpx.org/)
- [Tenacity Retry Guide](https://tenacity.readthedocs.io/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

---

## 🏆 Best Practices

### 1. Rate Limiting
- Respetar los límites de cada fuente
- Usar cache para reducir requests
- Implementar delays aleatorios

### 2. Error Handling
- Siempre usar fallback
- Log detallado de errores
- Circuit breaker para fuentes problemáticas

### 3. Monitoring
- Revisar `v_ingestion_health_status` diariamente
- Configurar alerts para success rate < 80%
- Mantener logs por 90 días

### 4. Security
- **NUNCA** commitear API keys al repo
- Usar GitHub Secrets para CI/CD
- Rotar API keys mensualmente

### 5. Performance
- Limitar concurrencia (max 10 simultáneos)
- Usar HTTP/2 para mejor throughput
- Cache habilitado siempre

---

**Mantenido por:** GameRadar AI Team  
**Última actualización:** 2026-04-16  
**Versión:** 1.0.0 (Military-Grade)

---

## 🎊 Conclusión

Sistema **100% listo para producción** con:

- ✅ 7+ fuentes estratégicas integradas
- ✅ Fallback automático resiliente
- ✅ GitHub Actions serverless ($0/mes)
- ✅ Logging completo a Supabase
- ✅ Anti-detection por región
- ✅ Circuit breaker y cache
- ✅ Documentación exhaustiva

**Status:** 🟢 Production Ready
