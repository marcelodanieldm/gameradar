# GameRadar AI - SaaS de Scouting para E-sports en Asia

## 🎯 Descripción

GameRadar AI es un sistema de ingesta masiva y scouting de jugadores de e-sports para regiones de Asia (India, Corea, Vietnam, etc.). El sistema scrappea datos de múltiples fuentes, los normaliza con soporte Unicode completo, y los almacena en una arquitectura Bronze/Silver/Gold.

## 🏗️ Arquitectura

### Stack Tecnológico
- **Backend**: Python 3.11+
- **Web Scraping**: Playwright (asíncrono)
- **Validación**: Pydantic con soporte Unicode
- **Base de Datos**: Supabase (PostgreSQL)
- **Integración**: Airtable API
- **Logging**: Loguru
- **Testing**: Playwright + Pytest (28 tests E2E)
- **Frontend**: Next.js 14, React 18, TypeScript 5.3, Tailwind CSS
- **CI/CD**: GitHub Actions (automation + testing)

### Arquitectura de Datos (Medallion)

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   BRONZE    │──────▶│    SILVER    │──────▶│    GOLD     │
│ (Raw Data)  │ auto │ (Normalized) │manual│ (Verified)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                      ┌──────────────┐
                      │  AIRTABLE    │
                      │   (Export)   │
                      └──────────────┘
```

**Bronze**: Datos crudos del scraping (JSONB)
- Trigger automático normaliza a Silver
- Soporte para múltiples fuentes

**Silver**: Datos normalizados y validados
- Campos estructurados con soporte Unicode
- Índices optimizados para búsqueda
- Detección automática de país

**Gold**: Datos verificados y enriquecidos
- Verificación manual opcional
- Talent Score calculado
- **GameRadar Score** calculado automáticamente (WinRate 40%, KDA 30%, Región 30%)
- Listo para análisis

## 📁 Estructura del Proyecto

```
gameradar/
├── models.py                    # Modelos Pydantic (PlayerProfile, Stats, etc)
├── config.py                    # Configuración centralizada
├── country_detector.py          # Detección de país por bandera/servidor
├── scrapers.py                  # Scrapers para Liquipedia, OP.GG, etc
├── bronze_ingestion.py          # 📦 Motor de ingesta Bronze (multi-fuente)
├── cnn_brasil_scraper.py        # 🥷 Ninja scraper para CNN Brasil
├── proxy_rotator.py             # Sistema de rotación de proxies
├── supabase_client.py           # Cliente de Supabase (Bronze/Silver/Gold)
├── airtable_client.py           # Cliente de Airtable
├── pipeline.py                  # Orquestación del flujo completo
├── database_schema.sql          # Esquema SQL de Supabase (Bronze/Silver/Gold)
├── gold_analytics.sql           # 📊 Analytics Layer - GameRadar Score avanzado
├── skill_vector_embeddings.py  # 🧠 Generador de embeddings (pgvector)
├── test_ninja_scraper.py        # Tests del scraper ninja
├── test_e2e_playwright.py       # 🧪 Tests E2E backend (11 tests)
├── conftest.py                  # Configuración de pytest
├── requirements.txt             # Dependencias Python
├── .env.example                 # Ejemplo de variables de entorno
├── .github/workflows/
│   ├── ninja_scraper.yml        # GitHub Actions workflow (CNN Brasil)
│   └── ingest.yml               # 🚀 Orquestador de ingesta automática (cada 6h)
├── frontend/
│   ├── components/
│   │   ├── TransculturalDashboard.tsx  # 🌍 Dashboard adaptativo regional
│   │   ├── RadarDashboard.tsx   # Dashboard principal
│   │   └── PlayerCard.tsx       # 🎨 UX Cultural (Mobile vs Technical)
│   ├── hooks/
│   │   └── useCountryDetection.ts  # 🌐 Detección automática de país
│   ├── messages/
│   │   ├── en.json              # 🇬🇧 English
│   │   ├── hi.json              # 🇮🇳 हिन्दी (Hindi)
│   │   ├── ko.json              # 🇰🇷 한국어 (Korean)
│   │   ├── ja.json              # 🇯🇵 日本語 (Japanese)
│   │   ├── vi.json              # 🇻🇳 Tiếng Việt (Vietnamese)
│   │   ├── zh.json              # 🇨🇳 中文 (Chinese)
│   │   └── th.json              # 🇹🇭 ไทย (Thai)
│   ├── tests/
│   │   └── e2e.spec.ts          # 🧪 Tests E2E frontend (17 tests)
│   ├── playwright.config.ts     # Configuración de Playwright
│   ├── package.json             # Dependencias Next.js
│   └── package.test.json        # Scripts de testing
├── README.md                    # Esta documentación
├── NINJA_SCRAPER.md            # 🥷 Guía del Ninja Scraper
└── E2E_TESTS.md                # 🧪 Guía de Tests E2E
```

## 🚀 Setup Inicial

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Instalar Playwright

```bash
playwright install chromium
```

### 3. Configurar Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Airtable
AIRTABLE_API_KEY=your-api-key
AIRTABLE_BASE_ID=your-base-id
AIRTABLE_TABLE_NAME=GameRadar_Players

# Scraper
RATE_LIMIT_DELAY=2
MAX_CONCURRENT_REQUESTS=5
```

### 4. Crear los Schemas en Supabase

#### Bronze/Silver/Gold Schema

Ejecutar el script `database_schema.sql` en el SQL Editor de Supabase (crea tablas base y triggers).

#### Analytics Layer (Gold)

Ejecutar el script `gold_analytics.sql` para:
- ✅ Tabla `gold_analytics` con componentes de score desglosados
- ✅ Función `calculate_gameradar_score_advanced()` con lógica regional
- ✅ Función `refresh_gold_analytics()` para recálculo diario
- ✅ Vistas analíticas (top players, breakdown regional)
- ✅ Trigger de auto-actualización desde Silver

### 5. Crear el Schema en Supabase (Original)

Ejecutar el script `database_schema.sql` en el SQL Editor de Supabase:

```sql
-- Copia y pega el contenido de database_schema.sql
```

Esto creará:
- ✅ Tablas Bronze/Silver/Gold con soporte Unicode
- ✅ Triggers automáticos de normalización
- ✅ Funciones de cálculo de Talent Score
- ✅ **Función de cálculo de GameRadar Score** (WinRate 40%, KDA 30%, Región 30%)
- ✅ Vistas de estadísticas por región
- ✅ Row Level Security (RLS)

## � Motor de Ingesta Bronze

### Script de Ingesta Automática

El sistema incluye `bronze_ingestion.py` - un scraper robusto diseñado para ingesta masiva:

**Características:**
- ✅ Playwright asíncrono con anti-detección
- ✅ Detección automática de caracteres asiáticos (Hangul, CJK, Hiragana/Katakana)
- ✅ Manejo de errores no-bloqueante (continúa si falla un jugador)
- ✅ Soporte multi-fuente (Liquipedia, OP.GG)
- ✅ Integración directa con Supabase Bronze layer
- ✅ Logging detallado con estadísticas

**Uso:**

```python
import asyncio
from bronze_ingestion import BronzeIngestionScraper

async def main():
    async with BronzeIngestionScraper(region="KR") as scraper:
        await scraper.run_ingestion(
            source="liquipedia",  # o "opgg"
            game="leagueoflegends",
            limit=50
        )

asyncio.run(main())
```

**Salida:**
```
🚀 INICIANDO INGESTA BRONZE
   Region: KR
   Source: liquipedia
   Game: leagueoflegends
📄 Scraping Liquipedia: https://liquipedia.net/leagueoflegends/Portal:Players
📊 Procesando 150 filas de la tabla
✓ Scraped 50 jugadores de Liquipedia
💾 Insertando 50 registros en Bronze...
✓ Insertados 50/50 registros en Bronze
✅ INGESTA COMPLETADA
📊 Resumen:
  - Scraped: 50
  - Insertados en Bronze: 50
  - Errores (no críticos): 0
  - Tasa de éxito: 100.0%
```

### GitHub Actions - Orquestador Automático

El archivo `.github/workflows/ingest.yml` ejecuta el scraper cada 6 horas:

**Características:**
- ✅ Ejecución automática (00:00, 06:00, 12:00, 18:00 UTC)
- ✅ Ejecución manual con parámetros configurables
- ✅ Multi-región en paralelo (KR, IN, VN, CN)
- ✅ CNN Brasil Ninja Scraper en job separado
- ✅ Fail-safe (continúa con otras regiones si una falla)
- ✅ Logs automáticos descargables
- ✅ Resumen ejecutivo con enlaces

**Setup:**

1. Configurar Secrets en GitHub:
   - `SUPABASE_URL`: Tu URL de Supabase
   - `SUPABASE_KEY`: Tu service role key
   - `PROXY_URL` (opcional): Para proxies rotativos

2. El workflow se ejecuta automáticamente cada 6 horas

3. Ejecutar manualmente:
   - `Actions` → `GameRadar AI Ingestion Engine` → `Run workflow`
   - Elegir región, fuente, y límite

**Costo:** ✅ 100% GRATIS con GitHub Actions (2,000 min/mes en repos públicos)

## �💻 Uso del Sistema

### Ejemplo 1: Scrapear jugadores de OP.GG Korea

```python
import asyncio
from scrapers import OPGGScraper

async def scrape_korean_players():
    async with OPGGScraper() as scraper:
        players = ["Faker", "Chovy", "ShowMaker"]
        profiles = await scraper.scrape_players(players)
        
        for profile in profiles:
            print(f"{profile.nickname}: {profile.stats.win_rate}% WR")

asyncio.run(scrape_korean_players())
```

### Ejemplo 2: Pipeline Completo

```python
import asyncio
from pipeline import GameRadarPipeline

async def run_pipeline():
    pipeline = GameRadarPipeline()
    
    korean_players = ["Faker", "Chovy", "Canyon"]
    
    # Ejecuta: Scraping -> Bronze -> Silver -> Gold -> Airtable
    await pipeline.run_full_pipeline(
        source="opgg",
        identifiers=korean_players,
        sync_to_airtable=True
    )

asyncio.run(run_pipeline())
```

### Ejemplo 3: Consultar datos de Supabase

```python
from supabase_client import SupabaseClient

db = SupabaseClient()

# Top jugadores de India
indian_players = db.get_players_by_country("IN", game="LOL", limit=10)

# Búsqueda difusa (soporte Unicode)
results = db.search_players_by_nickname_fuzzy("फेकर")  # Faker en Hindi

# Estadísticas por región
stats = db.get_stats_by_region()
```

### Ejemplo 4: Enviar a Airtable

```python
from airtable_client import AirtableClient
from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode

airtable = AirtableClient()

# Crear perfil
profile = PlayerProfile(
    nickname="TestPlayer",
    game=GameTitle.LEAGUE_OF_LEGENDS,
    country=CountryCode.INDIA,
    server="IN",
    rank="Diamond",
    stats=PlayerStats(win_rate=58.5, kda=3.2, games_analyzed=100),
    top_champions=[
        Champion(name="Yasuo", games_played=50, win_rate=60.0)
    ],
    profile_url="https://example.com"
)

# Enviar a Airtable
airtable.send_player(profile)
```

## 📊 Analytics Layer (Gold)

### Sistema de GameRadar Score Avanzado

El archivo `gold_analytics.sql` implementa un sistema completo de analytics con lógica regional:

**Función Principal: `calculate_gameradar_score_advanced()`**

```sql
SELECT * FROM calculate_gameradar_score_advanced(
    65.5,  -- win_rate
    4.2,   -- kda
    500,   -- games_played
    'KR',  -- region
    85.0   -- talent_score (opcional)
);

-- Resultado:
-- gameradar_score: 89.50
-- winrate_component: 26.20 (40%)
-- kda_component: 12.60 (30% para KR)
-- volume_component: 6.20 (10% para KR)
-- regional_multiplier: 1.20 (bonus Korea)
```

**Lógica Regional Implementada:**

| Región | Win Rate | KDA | Volume | Multiplier | Razón |
|--------|----------|-----|--------|------------|-------|
| **KR** | 40% | 30% | 10% | 1.20x | Alta competencia |
| **CN** | 40% | 30% | 10% | 1.15x | Alta competencia |
| **IN/VN/TH** | 40% | 15% | 30% | 1.0x | Priorizan grinders |
| **NA/EU/BR** | 40% | 30% | 10% | 1.05x | Competencia estándar |

**Características:**
- ✅ **Auto-actualización**: Trigger en `silver_players` → calcula automáticamente en `gold_analytics`
- ✅ **Histórico diario**: Campo `calculation_date` para tracking temporal
- ✅ **Transparencia**: Guarda desglose de cada componente
- ✅ **Normalización logarítmica**: Primeras partidas valen más (volumen)
- ✅ **Performance**: Índices en score, región, fecha

**Funciones de Consulta:**

```sql
-- Refrescar analytics manualmente
SELECT * FROM refresh_gold_analytics();
-- Retorna: players_processed, execution_time_ms

-- Ver top 100 global
SELECT * FROM vw_top_players_global;

-- Ver breakdown por región
SELECT * FROM vw_regional_score_breakdown;

-- Buscar score de jugador específico
SELECT * FROM get_player_score('faker_t1');
-- Retorna: nickname, gameradar_score, global_rank, regional_rank
```

**Programación Diaria:**

```sql
-- Opción 1: pg_cron (si tienes acceso superuser)
CREATE EXTENSION pg_cron;
SELECT cron.schedule(
    'refresh-analytics',
    '0 2 * * *',  -- 02:00 AM diario
    'SELECT refresh_gold_analytics();'
);

-- Opción 2: GitHub Actions (recomendado)
-- Agregar job en .github/workflows/analytics.yml
```

## 🎨 Frontend - UX Cultural

### PlayerCard Component

Componente React/Next.js con diseño dual adaptativo según región:

**Mobile-Heavy Card (India/Vietnam/Thailand):**
- ✅ Tarjeta táctil grande (responsive touch)
- ✅ Avatar 96px con score flotante
- ✅ Fuentes grandes con `font-devanagari` (Hindi/Vietnamita)
- ✅ Botón WhatsApp brillante (share pre-formateado)
- ✅ Stats grid con iconos coloridos
- ✅ Gradientes animados (purple/cyan/green)
- ✅ Hover/active feedback táctil

**Technical Card (Korea/Japan/China):**
- ✅ Layout minimalista tipo tabla
- ✅ Avatar compacto 48px
- ✅ Fuentes CJK optimizadas (`font-cjk`)
- ✅ Stats en formato grid compacto
- ✅ Colores sobrios (slate/cyan)
- ✅ Acciones minimalistas en footer

**Uso:**

```tsx
import PlayerCard from '@/components/PlayerCard';

<PlayerCard
  player_id="faker_t1"
  nickname="Faker"
  real_name="이상혁"
  country_code="KR"
  region="KR"
  game="LOL"
  rank="Challenger"
  avatar_url="https://..."
  profile_url="https://..."
  stats={{
    win_rate: 65.5,
    kda: 4.2,
    games_played: 500,
    talent_score: 95,
    gameradar_score: 98,
    main_role: "Mid",
    top_champions: ["Azir", "LeBlanc", "Orianna"]
  }}
  is_mobile_heavy={false}  // false = Technical, true = Mobile-Heavy
  is_verified={true}
/>
```

**Features:**
- ✅ WhatsApp Share nativo con mensaje pre-formateado
- ✅ Share API nativa (fallback)
- ✅ Copy ID con feedback visual
- ✅ Gradientes animados (e-sports vibe)
- ✅ Performance optimizado (sin re-renders)
- ✅ Accessibility completo

## 🌍 Soporte Unicode

El sistema soporta completamente caracteres Unicode para:

- 🇮🇳 **Hindi**: भारत, खिलाड़ी
- 🇰🇷 **Coreano**: 한국, 선수
- 🇨🇳 **Chino**: 中国, 玩家
- 🇻🇳 **Vietnamita**: Việt Nam, người chơi

Todas las tablas de PostgreSQL usan `VARCHAR` con encoding UTF-8, y Pydantic valida la integridad Unicode.

## 🔍 Detección de País

El sistema detecta automáticamente el país del jugador usando:

1. **Banderas emoji** en el perfil (🇮🇳 🇰🇷 🇻🇳 🇨🇳)
2. **Código de servidor** (kr, vn, mumbai, singapore)
3. **URL del perfil** (kr.op.gg, vn.op.gg)
4. **Nombre del país** en el texto

Prioridad: Bandera > Servidor > URL > Texto

## 📊 Modelos de Datos

### PlayerProfile (Principal)

```python
PlayerProfile(
    nickname="Faker",
    game=GameTitle.LEAGUE_OF_LEGENDS,
    country=CountryCode.KOREA,
    server="KR",
    rank="Challenger",
    stats=PlayerStats(
        win_rate=65.5,
        kda=4.8,
        games_analyzed=100
    ),
    top_champions=[
        Champion(name="Azir", games_played=50, win_rate=70.0),
        Champion(name="LeBlanc", games_played=30, win_rate=65.0),
        Champion(name="Orianna", games_played=20, win_rate=60.0)
    ],
    profile_url="https://kr.op.gg/summoners/kr/Faker"
)
```

## 🛠️ Scrapers Disponibles

| Scraper | Región | Juegos | Status |
|---------|--------|--------|--------|
| **Bronze Ingestion** 📦 | Multi-región | LOL | ✅ Producción |
| **OP.GG** | KR, VN | League of Legends | ✅ Implementado |
| **Liquipedia** | India, SEA | LOL, Dota2, CSGO | ✅ Implementado |
| **CNN Brasil** 🥷 | Global | E-sports | ✅ Ninja Mode |
| **Valorant Tracker** | Asia | Valorant | 🚧 Pendiente |
| **Dotabuff** | Asia | Dota 2 | 🚧 Pendiente |

### 🥷 Ninja Scraper (GitHub Actions)

El scraper ninja automatizado se ejecuta cada 6 horas:
- **Fuente**: CNN Brasil E-sports
- **Modo**: Stealth con anti-detección
- **Proxy**: Rotación automática (opcional)
- **Tags**: Detecta "Region: India" automáticamente
- **Docs**: Ver [NINJA_SCRAPER.md](NINJA_SCRAPER.md)

## 📈 Database Schema

### Tablas Principales

```sql
bronze_raw_data       -- Datos crudos (JSONB)
  ↓ (trigger automático)
silver_players        -- Datos normalizados
  ↓ (promoción manual)
gold_verified_players -- Datos verificados
```

### Funciones SQL

**Schema Base (database_schema.sql):**
- `normalize_bronze_to_silver()`: Normalización automática
- `calculate_talent_score()`: Calcula score 0-100
- `calculate_gameradar_score()`: GameRadar Score básico (WinRate 40%, KDA 30%, Región 30%)
- `update_updated_at_column()`: Mantiene timestamps

**Analytics Layer (gold_analytics.sql):**
- `calculate_gameradar_score_advanced()`: **Score avanzado con lógica regional**
  - **WinRate 40%**: Componente directo del porcentaje de victorias
  - **KDA Variable**: 30% (KR/CN/JP) o 15% (IN/VN/TH)
  - **Volume Variable**: 10% (KR/CN/JP) o 30% (IN/VN/TH) - priorizan grinders
  - **Talent Score 20%**: Bonus basado en talent_score existente
  - **Regional Multiplier**: KR=1.2x, CN=1.15x, JP=1.1x, IN/VN/TH=1.0x
  - **Retorna**: Score + desglose de componentes para transparencia
- `refresh_gold_analytics()`: Recalcula toda la tabla gold_analytics desde silver_players
- `get_player_score(player_id)`: Obtiene score + rankings global/regional

### Vistas

**Schema Base:**
- `vw_top_players_by_country`: Ranking por país
- `vw_stats_by_region`: Estadísticas agregadas

**Analytics Layer:**
- `vw_top_players_global`: Top 100 jugadores globales por GameRadar Score
- `vw_top_players_by_region`: Rankings regionales con rank_in_region
- `vw_regional_score_breakdown`: Comparación de componentes de score por región

## 🔐 Seguridad

- Row Level Security (RLS) habilitado
- Políticas de lectura para usuarios autenticados
- Escritura solo para admins
- API Keys en variables de entorno

## 🐛 Debugging

```python
# Activar logging verbose
from loguru import logger

logger.add("debug.log", level="DEBUG", rotation="10 MB")
```

## 📝 Notas de Desarrollo

### Rate Limiting
- Delay de 2s entre requests (configurable)
- Max 5 requests concurrentes

### Retry Logic
- 3 intentos automáticos con backoff exponencial
- Manejo de errores graceful

### Performance
- Scraping asíncrono con Playwright
- Índices GIN en JSONB para búsqueda rápida
- Búsqueda difusa con pg_trgm

## 🧪 Testing

### Suite de Tests E2E con Playwright

GameRadar AI incluye **28 tests end-to-end** que validan todas las funcionalidades:

#### Backend Tests (Python)

**Archivo**: `test_e2e_playwright.py` - **11 tests**

```bash
# Instalar dependencias
pip install pytest pytest-asyncio
playwright install chromium

# Ejecutar tests
python test_e2e_playwright.py
```

**Coverage:**
- ✅ Bronze Ingestion (Liquipedia + OP.GG)
- ✅ Country Detection (bandera, servidor, URL, texto)
- ✅ Supabase Integration (Bronze → Silver → Gold)
- ✅ Asian Character Detection (Coreano/Chino/Japonés)
- ✅ Error Handling no-bloqueante
- ✅ Search & Queries
- ✅ Performance (<30s)

#### Frontend Tests (TypeScript)

**Archivo**: `frontend/tests/e2e.spec.ts` - **17 tests**

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install

# Ejecutar tests
npm run test:e2e              # Headless
npm run test:e2e:headed       # Con navegador visible
npm run test:e2e:ui           # Modo interactivo
npm run test:e2e:debug        # Debug mode
```

**Coverage:**
- ✅ Dashboard rendering & stats cards
- ✅ PlayerCard adaptativo (Mobile-Heavy vs Technical)
- ✅ View mode toggle (Auto/Cards/Table)
- ✅ Region filter & sorting
- ✅ Responsive design (Desktop/Tablet/Mobile)
- ✅ Dark mode
- ✅ Loading & error states
- ✅ Accessibility (keyboard, alt text)
- ✅ Performance (<5s load time)
- ✅ Supabase data fetching

**Tests Multi-Browser:**
- Chromium (Desktop + Mobile)
- Firefox
- WebKit (Safari)
- Microsoft Edge

### Resultados Esperados

```bash
# Backend
==============================================================
🚀 GAMERADAR AI - E2E TESTS
==============================================================
✅ Passed: 11/11
❌ Failed: 0/11
==============================================================

# Frontend
Running 17 tests using 4 workers
  ✓ [chromium] › Dashboard debe renderizar correctamente
  ✓ [chromium] › Stats cards deben mostrar datos
  ...
  17 passed (45s)
```

**Documentación completa**: Ver [E2E_TESTS.md](E2E_TESTS.md)

---

## 🧠 Sprint 2: Motor de Inteligencia Semántica y UX Regional

### Paradigma
- **Semantic Search:** Pasamos de filtros estáticos (SQL WHERE) a búsqueda por significado usando vectores.
- **Adaptive UI:** La interfaz muta según la región del usuario para maximizar retención y engagement.

### Entregables

#### 1. Motor de Búsqueda Semántica (pgvector)

**Tecnologías:**
- PostgreSQL + extensión `pgvector`
- Vectores de 4 dimensiones: `[KDA, WinRate, Agresividad, Versatilidad]`
- Búsqueda por similitud usando cosine distance

**Arquitectura:**

```
┌──────────────────────────────────────┐
│  silver_players                      │
│  ├─ win_rate                         │
│  ├─ kda                              │
│  ├─ kills_avg, deaths_avg            │
│  └─ top_champions                    │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│  skill_vector_embeddings.py          │
│  ├─ Normalización (0-1)              │
│  ├─ Heurísticas de agresividad       │
│  └─ Cálculo de versatilidad          │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│  gold_analytics                      │
│  ├─ skill_vector vector(4)           │
│  ├─ idx_gold_skill_vector (IVFFlat)  │
│  └─ search_similar_players()         │
└──────────────────────────────────────┘
```

**Uso del Motor:**

```bash
# 1. Generar embeddings para todos los jugadores
python skill_vector_embeddings.py --limit 500

# 2. Filtrar por país/juego
python skill_vector_embeddings.py --country IN --game LOL --limit 100

# 3. Dry run (no escribe en DB)
python skill_vector_embeddings.py --dry-run
```

**Búsqueda de Jugadores Similares:**

```sql
-- Buscar los 10 jugadores más similares a un perfil
SELECT 
    nickname,
    country_code,
    similarity,
    gameradar_score,
    win_rate,
    kda
FROM search_similar_players(
    '[0.5, 0.7, 0.3, 0.8]'::vector(4),  -- Vector de consulta
    10,                                  -- Límite de resultados
    'KR',                                -- Filtro por país (opcional)
    'LOL'                                -- Filtro por juego (opcional)
);
```

**Componentes del Vector:**

| Dimensión | Descripción | Rango | Cálculo |
|-----------|-------------|-------|---------|
| **KDA** | Kill/Death/Assist ratio | 0-1 | `kda / 10` (normalizado) |
| **WinRate** | Porcentaje de victorias | 0-1 | `win_rate / 100` |
| **Agresividad** | Ratio kills/deaths | 0-1 | `(kills_avg / (deaths_avg + 1)) / 5` |
| **Versatilidad** | Diversidad de campeones | 0-1 | `len(top_champions) / 3` |

**Ventajas:**
- ✅ Encuentra jugadores con perfiles de habilidad similares entre regiones
- ✅ No depende de palabras clave exactas
- ✅ Búsqueda en O(log n) con índice IVFFlat
- ✅ Filtros opcionales por país/juego
- ✅ Score de similitud (0-1) incluido en resultados

---

#### 2. UX Regional Adaptativa (3 Vistas)

**Hook de Detección:** `useCountryDetection()`
- Estrategia 1: Browser locale (`navigator.language`)
- Estrategia 2: IP geolocation (ipapi.co)
- Estrategia 3: Fallback a análisis de dataset

**Vista 1: India/Vietnam Feed** 🇮🇳🇻🇳

```typescript
// Países: IN, VN, TH, PH, ID
// Características:
- Feed vertical estilo red social
- GameRadar Score PROMINENTE (text-6xl)
- Botones de acción grandes:
  → WhatsApp (India)
  → Zalo (Vietnam)
- Stats en cards grandes y legibles
- Tipografía robusta: font-devanagari para Hindi
- Gradientes llamativos y colores saturados
```

**UX Rationale:**
- Mobile-first: 80%+ del tráfico en mobile en India/Vietnam
- Contacto directo: Cultura de comunicación instantánea (WhatsApp/Zalo)
- Visual: Menos densidad de datos, más impacto visual

**Vista 2: Korea/China Dense Table** 🇰🇷🇨🇳

```typescript
// Países: KR, CN
// Características:
- Tabla técnica de alta densidad
- Fuentes compactas (text-xs, text-[10px])
- Micro-stats visibles:
  → WR%, KDA, Games, Champions
  → Sorting en todas las columnas
- Clase font-cjk para caracteres CJK
- Hover effects con borde cyan
- Info máxima en mínimo espacio
```

**UX Rationale:**
- Data-driven: Cultura analítica, valoran estadísticas completas
- Desktop-first: Mayoría accede desde PC gaming
- Eficiencia: Quieren ver 50+ jugadores sin scroll

**Vista 3: Japan Minimalist View** 🇯🇵

```typescript
// País: JP
// Características:
- Diseño limpio con mucho espacio en blanco
- Tooltips explicativos para cada métrica:
  → "Talent Score: Overall player skill rating..."
  → "Win Rate: Percentage of games won..."
  → "KDA: Kill/Death/Assist ratio..."
- Fuentes light (font-light)
- Bordes sutiles (border-slate-800/30)
- Animaciones suaves (duration-500)
- Componente MetricCard con Info icon
```

**UX Rationale:**
- Trust-building: Cultura de transparencia y educación
- Minimalismo: Diseño zen, menos es más
- Explicación: Valoran entender el "por qué" de cada métrica

---

#### 3. Sistema de Internacionalización (i18n)

**Framework:** `next-intl`
- ✅ Cambio de idioma sin recarga de página
- ✅ 7 idiomas soportados
- ✅ Traducción de componentes con `useTranslations()`

**Idiomas Implementados:**

| Código | Idioma | Script | Font |
|--------|--------|--------|------|
| `en` | English | Latin | Default |
| `hi` | हिन्दी | Devanagari | Noto Sans Devanagari |
| `ko` | 한국어 | Hangul | Noto Sans CJK KR |
| `ja` | 日本語 | Kanji/Hiragana | Noto Sans CJK JP |
| `vi` | Tiếng Việt | Latin + diacríticos | Default |
| `zh` | 中文 | Hanzi | Noto Sans CJK SC |
| `th` | ไทย | Thai | Noto Sans Thai |

**Uso en Componentes:**

```tsx
import { useTranslations } from 'next-intl';

function MyComponent() {
  const t = useTranslations('dashboard');
  
  return (
    <h1>{t('title')}</h1>
    <p>{t('stats.totalPlayers')}</p>
  );
}
```

**Estructura de Traducciones:**

```json
{
  "dashboard": {
    "viewMode": { "auto", "feed", "dense", "minimal" },
    "loading": "..."
  },
  "feed": {
    "gameRadarScore": "...",
    "contactWhatsApp": "..."
  },
  "denseTable": {
    "nickname": "...",
    "winRate": "..."
  },
  "minimal": {
    "talentScoreTooltip": "...",
    "kdaTooltip": "..."
  }
}
```

---

#### 4. Lógica de Selección Automática

```typescript
function determineRegionalView(): RegionalView {
  switch (countryCode) {
    case "IN", "VN", "TH", "PH", "ID":
      return "feed";      // Mobile-heavy regions
    
    case "KR", "CN":
      return "dense";     // Data-driven regions
    
    case "JP":
      return "minimal";   // Trust-building UX
    
    default:
      // Fallback: analizar is_mobile_heavy en dataset
      if (mobileHeavyCount > 50%) return "feed";
      return "dense";
  }
}
```

**Override Manual:**
- 🌐 Auto (detección automática)
- 📱 Feed (estilo social)
- 📊 Dense (tabla técnica)
- 🎨 Minimal (japonés)

---

### Especificaciones Técnicas

**Base de Datos (gold_analytics):**
```sql
CREATE EXTENSION IF NOT EXISTS "vector";

ALTER TABLE gold_analytics 
ADD COLUMN skill_vector vector(4);

CREATE INDEX idx_gold_skill_vector 
ON gold_analytics 
USING ivfflat (skill_vector vector_cosine_ops)
WITH (lists = 100);
```

**Frontend (TransculturalDashboard.tsx):**
- 3 componentes especializados:
  - `IndiaVietnamFeed`
  - `KoreaChinaDenseTable`
  - `JapanMinimalistView`
- Hook `useCountryDetection()` con fallback
- Hook `useTranslations()` para i18n
- Clases Tailwind adaptativas:
  - `font-devanagari` (Hindi)
  - `font-cjk` (Korean/Chinese/Japanese)
  - `font-light` vs `font-black` según región

**Archivos Modificados:**
- ✅ `gold_analytics.sql` - pgvector + search_similar_players()
- ✅ `skill_vector_embeddings.py` - Generador de embeddings
- ✅ `frontend/components/TransculturalDashboard.tsx` - 3 vistas
- ✅ `frontend/hooks/useCountryDetection.ts` - Detección de país
- ✅ `frontend/messages/*.json` - 7 archivos de traducción

**Documentación Adicional:**
- Ver [SPRINT2_SUMMARY.md](SPRINT2_SUMMARY.md) para guía completa
- Ver [skill_vector_embeddings.py](skill_vector_embeddings.py) para heurísticas de embeddings

---

## 🎯 Roadmap

- [x] **Motor de Ingesta Bronze** - Scraper robusto multi-fuente implementado
- [x] **GitHub Actions Automation** - Orquestador cada 6 horas (gratis)
- [x] **GameRadar Score Básico** - Lógica de negocio implementada (WinRate+KDA+Región)
- [x] **GameRadar Score Avanzado** - Analytics Layer con lógica regional variable
- [x] **Frontend UX Cultural** - PlayerCard adaptativo (Mobile vs Technical)
- [x] **Transcultural Dashboard** - Consume silver_players con UI adaptativa
- [x] **E2E Tests** - 28 tests con Playwright (Backend + Frontend)
- [x] **Sprint 2: Motor de Inteligencia Semántica** - pgvector + embeddings + búsqueda por similitud
- [x] **Sprint 2: UX Regional Adaptativa** - 3 vistas diferenciadas (India/Vietnam, Korea/China, Japan)
- [x] **Sprint 2: Sistema i18n** - Traducción dinámica para 7 idiomas con next-intl
- [ ] Dashboard web completo con visualizaciones (Next.js - en progreso)
- [ ] API REST para búsqueda semántica
- [ ] Soporte para Valorant
- [ ] Scraper de Dotabuff
- [ ] Machine Learning para predicción de talento
- [ ] API REST pública
- [ ] Webhooks para actualizaciones en tiempo real
- [ ] Sistema de notificaciones (WhatsApp/Email)

## 📞 Soporte

Para issues o preguntas, contactar al equipo de Data Science & Backend.

---

**Vibe**: Código limpio, modular y listo para escalar 🚀
