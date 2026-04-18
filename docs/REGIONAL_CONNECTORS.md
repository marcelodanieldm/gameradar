# 🌏 Regional Connectors - Expansión de Capa Bronze

## 📋 Descripción

Módulo profesional de conectores regionales para expandir la capa Bronze de GameRadar AI con scrapers especializados para mercados asiáticos.

### Conectores Implementados

1. **DakGGConnector** - Corea del Sur 🇰🇷
   - Fuente: [Dak.gg](https://dak.gg)
   - Juegos: League of Legends, VALORANT
   - Soporte: Caracteres Hangul (한글)

2. **ScoreGGConnector** - China 🇨🇳
   - Fuente: [ScoreGG.com](https://www.scoregg.com)
   - Juegos: League of Legends, Dota 2
   - Soporte: Caracteres Chinos (中文)
   - **Feature especial**: Sistema de proxy rotativo para bypass de Great Firewall

## ✨ Características Principales

### 🔄 Sistema de Proxy Rotativo para China
- **ChinaProxyRotator**: Rotación automática de proxies
- Detección y marcado de proxies fallidos
- User-Agents aleatorios específicos para China
- Configuración de headers localizada

### 🛡️ Resiliencia y Reintentos
- **Tenacity integration**: Reintentos automáticos con backoff exponencial
- Dak.gg: 3 intentos con backoff de 4-30 segundos
- ScoreGG: 5 intentos con backoff de 4-60 segundos
- Manejo robusto de timeouts y errores de red

### 🤖 Cumplimiento Ético
- **RobotsTxtChecker**: Verificación automática de robots.txt
- Respeto a las reglas de cada sitio web
- User-Agent identificable: "GameRadarBot"
- Delays aleatorios para simular comportamiento humano

### 🎯 Extracción de Datos
Campos extraídos para cada jugador:
- ✅ **WinRate** - Porcentaje de victorias
- ✅ **Most Played Hero** - Campeón/Héroe más jugado
- ✅ KDA (Kills/Deaths/Assists)
- ✅ Rank/Tier
- ✅ Nickname (soporte Unicode completo)
- ✅ Top 3 champions con stats individuales

### 📦 Integración con Supabase
- Mapeo automático al formato JSON de Bronze
- Inserción directa en `bronze_raw_data`
- Soporte para triggers de normalización a Silver

## 🚀 Uso

### Instalación

```bash
pip install playwright tenacity loguru pydantic
playwright install chromium
```

### Ejemplo Básico: Dak.gg (Corea)

```python
from RegionalConnectors import DakGGConnector

async with DakGGConnector() as connector:
    # Scrapear un jugador
    profile = await connector.scrape_player("Faker", game="lol")
    
    # Insertar en Bronze
    await connector.insert_to_bronze(profile, "dak.gg")
```

### Ejemplo Básico: ScoreGG (China)

```python
from RegionalConnectors import ScoreGGConnector

async with ScoreGGConnector(use_proxy=True) as connector:
    # Scrapear un jugador con proxy rotativo
    profile = await connector.scrape_player("player123", game="lol")
    
    # Insertar en Bronze
    await connector.insert_to_bronze(profile, "scoregg.com")
```

### Ejemplo Avanzado: Batch Scraping

```python
from RegionalConnectors import scrape_dak_gg_players, scrape_scoregg_players

# Scrapear múltiples jugadores de Corea
korean_players = ["Faker", "ShowMaker", "Chovy", "Canyon", "Keria"]
dak_profiles = await scrape_dak_gg_players(korean_players, game="lol")

# Scrapear múltiples jugadores de China con proxy
chinese_players = ["player1", "player2", "player3"]
scoregg_profiles = await scrape_scoregg_players(
    chinese_players, 
    game="lol", 
    use_proxy=True
)
```

## ⚙️ Configuración de Proxies para China

### Opción 1: Proxies Premium (Recomendado)

Editar `RegionalConnectors.py` y actualizar `ChinaProxyRotator.CHINA_PROXIES`:

```python
CHINA_PROXIES = [
    {
        "server": "http://your-proxy-1.com:8080",
        "username": "your_username",
        "password": "your_password"
    },
    {
        "server": "http://your-proxy-2.com:8080",
        "username": "your_username", 
        "password": "your_password"
    },
    # Añadir más proxies para mejor rotación
]
```

### Opción 2: Servicios de Proxy Comerciales

Integración con servicios como:
- **Bright Data** (Luminati)
- **ScraperAPI**
- **Oxylabs**
- **Smartproxy**

## 📊 Formato de Datos

### Entrada (Scraping)
```python
summoner_name = "Faker"  # o player_id para ScoreGG
game = "lol"  # lol, valorant, dota2
```

### Salida (Bronze Layer)
```json
{
  "raw_data": {
    "nickname": "Faker",
    "game": "LOL",
    "country": "KR",
    "server": "KR",
    "rank": "Challenger",
    "stats": {
      "win_rate": 67.5,
      "kda": 4.8,
      "games_analyzed": 100
    },
    "top_champions": [
      {
        "name": "Azir",
        "games_played": 50,
        "win_rate": 72.0
      },
      {
        "name": "LeBlanc",
        "games_played": 30,
        "win_rate": 65.0
      }
    ],
    "profile_url": "https://dak.gg/lol/profile/Faker",
    "scraped_at": "2026-04-16T18:30:00Z"
  },
  "source": "dak.gg",
  "source_url": "https://dak.gg/lol/profile/Faker",
  "processing_status": "pending"
}
```

## 🧪 Testing

```bash
# Ejecutar tests
python test_regional_connectors.py

# Ver logs
tail -f test_regional_connectors_*.log
```

## 🔍 Selectores Web

### Dak.gg
Los selectores están optimizados para la estructura actual (2026) de Dak.gg:
- Nickname: `h1`, `.summoner-name`, `[class*='name']`
- Rank: `.tier`, `[class*='tier']`, `[class*='rank']`
- WinRate: `.win-rate`, `[class*='winrate']`
- Champions: `.champion-list .champion`, `[class*='most-played']`

### ScoreGG
Selectores con soporte para caracteres chinos:
- Nickname: `h1`, `.player-name`, `[class*='name']`
- Rank: `.tier`, `[class*='tier']`
- WinRate: `[class*='winrate']`, `[class*='胜率']` (胜率 = win rate en chino)
- Champions: `[class*='hero']`, `[class*='英雄']` (英雄 = hero en chino)

## 📈 Métricas y Logging

El módulo registra automáticamente:
- ✅ Jugadores scraped exitosamente
- ❌ Errores y reintentos
- 🔄 Rotación de proxies
- 🚫 Bloqueos por robots.txt
- ⏱️ Tiempos de respuesta

Logs guardados en: `regional_connectors_{timestamp}.log`

## 🛠️ Troubleshooting

### Problema: Timeouts en ScoreGG
**Solución**: Habilitar proxies y aumentar timeout:
```python
async with ScoreGGConnector(use_proxy=True) as connector:
    # Los timeouts ya están configurados en 45s para China
    profile = await connector.scrape_player("player123", game="lol")
```

### Problema: Proxies fallando
**Solución**: El sistema automáticamente marca proxies fallidos y rota al siguiente. Asegúrate de tener al menos 3-5 proxies configurados.

### Problema: robots.txt bloquea scraping
**Solución**: El módulo respeta robots.txt por defecto. Si el sitio permite el scraping pero con rate limiting, ajusta los delays:
```python
# En el código, ajustar:
await asyncio.sleep(random.uniform(4, 8))  # Aumentar delay
```

## 🔐 Seguridad

- ✅ No se guardan credenciales en código (usar variables de entorno)
- ✅ Rotación automática de User-Agents
- ✅ Anti-detección con scripts de obfuscación
- ✅ Respeto a robots.txt
- ✅ Rate limiting con delays aleatorios

## 📚 Arquitectura

```
RegionalConnectors.py
│
├── ChinaProxyRotator          # Sistema de proxy para China
│   ├── get_next_proxy()       # Rotación de proxies
│   └── mark_proxy_failed()    # Marcado de proxies fallidos
│
├── RobotsTxtChecker           # Verificador ético
│   └── can_fetch()            # Verifica robots.txt
│
├── BaseRegionalConnector      # Clase base abstracta
│   ├── __aenter__/__aexit__   # Context manager
│   ├── _create_stealth_page() # Anti-detección
│   ├── insert_to_bronze()     # Inserción en Supabase
│   └── scrape_player()        # Método abstracto
│
├── DakGGConnector            # Conector para Corea
│   └── scrape_player()       # Implementación específica
│
└── ScoreGGConnector          # Conector para China
    └── scrape_player()       # Con proxy rotativo
```

## 🚦 Roadmap

- [ ] Añadir soporte para más sitios asiáticos
- [ ] Implementar caché de perfiles para evitar re-scraping
- [ ] Dashboard de monitoreo de proxies
- [ ] Integración con más servicios de proxy premium
- [ ] Soporte para más juegos (Mobile Legends, PUBG Mobile)

## 📝 Changelog

### v1.0.0 (2026-04-16)
- ✅ Implementación inicial
- ✅ DakGGConnector (Corea)
- ✅ ScoreGGConnector (China)
- ✅ Sistema de proxy rotativo
- ✅ Verificador de robots.txt
- ✅ Integración con Supabase Bronze

## 👥 Contribuciones

Para añadir un nuevo conector regional:

1. Heredar de `BaseRegionalConnector`
2. Implementar `scrape_player()`
3. Configurar selectores específicos del sitio
4. Añadir configuración de proxy si es necesario
5. Actualizar tests

## 📄 Licencia

Parte del proyecto GameRadar AI - Data Engineering Team
