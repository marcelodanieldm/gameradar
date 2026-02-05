# GameRadar AI - SaaS de Scouting para E-sports en Asia

## 🎯 Descripción

GameRadar AI es un sistema de ingesta masiva y scouting de jugadores de e-sports para regiones de Asia (India, Corea, Vietnam, etc.). El sistema scrappea datos de múltiples fuentes, los normaliza con soporte Unicode completo, y los almacena en una arquitectura Bronze/Silver/Gold.

## 🏗️ Arquitectura

### Stack Tecnológico
- **Backend**: Python 3.9+
- **Web Scraping**: Playwright (asíncrono)
- **Validación**: Pydantic con soporte Unicode
- **Base de Datos**: Supabase (PostgreSQL)
- **Integración**: Airtable API
- **Logging**: Loguru

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
├── cnn_brasil_scraper.py        # 🥷 Ninja scraper para CNN Brasil
├── proxy_rotator.py             # Sistema de rotación de proxies
├── supabase_client.py           # Cliente de Supabase (Bronze/Silver/Gold)
├── airtable_client.py           # Cliente de Airtable
├── pipeline.py                  # Orquestación del flujo completo
├── database_schema.sql          # Esquema SQL de Supabase
├── test_ninja_scraper.py        # Tests del scraper ninja
├── requirements.txt             # Dependencias Python
├── .env.example                 # Ejemplo de variables de entorno
├── .github/workflows/
│   └── ninja_scraper.yml        # GitHub Actions workflow
├── README.md                    # Esta documentación
└── NINJA_SCRAPER.md            # 🥷 Guía del Ninja Scraper
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

### 4. Crear el Schema en Supabase

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

## 💻 Uso del Sistema

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

- `normalize_bronze_to_silver()`: Normalización automática
- `calculate_talent_score()`: Calcula score 0-100
- `calculate_gameradar_score()`: **GameRadar Score con precisión matemática**
  - **WinRate 40%**: Componente directo del porcentaje de victorias
  - **KDA 30%**: Normalizado (KDA × 20, máximo 100)
  - **Región 30%**: Multiplicador de dificultad (Corea=1.2, India=1.0)
  - **Resultado**: Escala 0-100, persiste automáticamente en Gold layer
- `update_updated_at_column()`: Mantiene timestamps

### Vistas

- `vw_top_players_by_country`: Ranking por país
- `vw_stats_by_region`: Estadísticas agregadas

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

## 🎯 Roadmap

- [ ] Soporte para Valorant
- [ ] Scraper de Dotabuff
- [ ] Machine Learning para predicción de talento
- [x] **GameRadar Score** - Lógica de negocio implementada (WinRate+KDA+Región)
- [ ] Dashboard web con visualizaciones (Next.js - en progreso)
- [ ] API REST pública
- [ ] Webhooks para actualizaciones en tiempo real

## 📞 Soporte

Para issues o preguntas, contactar al equipo de Data Science & Backend.

---

**Vibe**: Código limpio, modular y listo para escalar 🚀
