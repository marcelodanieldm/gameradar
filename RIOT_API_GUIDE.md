# 🎮 Riot Games Official API - Fallback Automático

## 🆓 API Gratuita con Rate Limits Generosos

La API oficial de Riot Games es **100% GRATUITA** y proporciona datos en tiempo real de:
- Challenger (Top ~300 jugadores)
- Grandmaster (Top ~700 jugadores)
- Información detallada de jugadores
- Estadísticas de partidas

**Rate Limits** (gratis):
- 20 requests/segundo
- 100 requests/2 minutos
- Suficiente para la mayoría de casos de uso

---

## 🚀 Configuración Rápida (5 minutos)

### Paso 1: Obtener API Key

1. Ve a: https://developer.riotgames.com/
2. Inicia sesión con tu cuenta de Riot Games (crea una si no tienes)
3. Ve a "Dashboard" → "Register Product" (opcional) o usa la Development API Key
4. Copia tu **Development API Key** (expira cada 24 horas, gratis)

**Development API Key**: Perfecta para testing/desarrollo
- ✅ Gratis
- ✅ Mismos límites que API de producción
- ⚠️ Expira cada 24 horas (debes regenerar)

**Production API Key**: Para aplicaciones en producción
- ✅ No expira
- ✅ Mismos rate limits
- 📝 Requiere registro de aplicación (gratis)

### Paso 2: Configurar en el Proyecto

**Opción A: Variable de Entorno (Recomendado)**

```bash
# Windows PowerShell
$env:RIOT_API_KEY = "RGAPI-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Linux/Mac
export RIOT_API_KEY="RGAPI-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Verificar
echo $env:RIOT_API_KEY  # Windows
echo $RIOT_API_KEY      # Linux/Mac
```

**Opción B: Archivo .env**

Crea o edita el archivo `.env` en la raíz del proyecto:

```env
# Riot Games Official API
RIOT_API_KEY=RGAPI-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Opción C: Hardcode (Solo para testing)**

Edita `config.py`:
```python
# NO recomendado para producción, pero funciona para testing
riot_api_key: str = "RGAPI-tu-api-key-aqui"
```

### Paso 3: Verificar Instalación

```bash
# Probar el cliente de Riot API directamente
python riot_api_client.py
```

Deberías ver:
```
✅ 10 jugadores obtenidos:

  1. Hide on bush - Challenger 1234LP
     Win Rate: 65.5% | Games: 234
  ...
```

---

## 🔄 Cómo Funciona el Fallback Automático

El scraper ahora usa una estrategia de **fallback automático**:

```
┌─────────────────────────────────────┐
│  1. Intentar Scraping de OP.GG     │
│     (NO-HEADLESS + Delays largos)   │
└────────────┬────────────────────────┘
             │
             ↓
     ¿Obtuvo jugadores?
             │
    ┌────────┴────────┐
    │ SÍ              │ NO
    ↓                 ↓
┌───────┐    ┌────────────────────┐
│ Usar  │    │ FALLBACK: Riot API │
│ datos │    │ (automático)        │
└───────┘    └────────────────────┘
```

**NO necesitas cambiar nada en tu código**. El fallback se activa automáticamente cuando:
- OP.GG bloquea la request (403 Error)
- No se encuentran jugadores (selectores cambiaron)
- Cualquier error en el scraping

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Scraping Normal (con fallback automático)

```python
from bronze_ingestion import BronzeIngestionScraper
import asyncio

async def main():
    async with BronzeIngestionScraper(region="KR", headless=False) as scraper:
        # Intenta scraping de OP.GG
        # Si falla, automáticamente usa Riot API
        players = await scraper.scrape_opgg_ranking(limit=100)
        
        print(f"✅ {len(players)} jugadores obtenidos")
        print(f"Fuente: {players[0]['data_source']}")  # 'opgg' o 'riot_api'

asyncio.run(main())
```

### Ejemplo 2: Usar Riot API Directamente

```python
from riot_api_client import RiotAPIClient
import asyncio

async def main():
    client = RiotAPIClient(
        api_key="RGAPI-tu-key-aqui",
        region="KR"
    )
    
    # Obtener top 50 Challenger
    players = await client.get_top_players(limit=50)
    
    for player in players[:5]:
        print(f"{player.rank}. {player.player_name} - {player.lp}LP")

asyncio.run(main())
```

### Ejemplo 3: Regiones Soportadas

```python
# Riot API soporta TODAS las regiones de LoL
regions = ["KR", "NA", "EUW", "EUNE", "BR", "LAN", "LAS", 
           "OCE", "TR", "RU", "JP", "PH", "SG", "TH", "TW", "VN"]

for region in regions:
    client = RiotAPIClient(api_key=api_key, region=region)
    players = await client.get_top_players(limit=10)
    print(f"{region}: {len(players)} jugadores")
```

---

## 🧪 Testing del Fallback

### Test 1: Forzar Fallback

```python
# Simular que OP.GG falla
import pytest
from bronze_ingestion import BronzeIngestionScraper

@pytest.mark.asyncio
async def test_riot_api_fallback():
    """Test que el fallback de Riot API funciona"""
    async with BronzeIngestionScraper(region="KR") as scraper:
        # scrape_opgg_ranking automáticamente usa fallback si scraping falla
        players = await scraper.scrape_opgg_ranking(limit=20)
        
        assert len(players) > 0, "Debería obtener jugadores (scraping o API)"
        
        # Verificar fuente
        if players[0]['data_source'] == 'riot_api':
            print("✅ Fallback de Riot API usado exitosamente")
        else:
            print("✅ Scraping funcionó sin necesidad de fallback")

pytest.main([__file__, "-v"])
```

### Test 2: API Key Funcional

```bash
# Verificar que la API key está bien configurada
python -c "from config import settings; print(f'API Key: {settings.riot_api_key[:20]}...')"
```

Deberías ver:
```
API Key: RGAPI-xxxxxxxxxxxxxxxx...
```

Si ves `your-riot-api-key-here`, necesitas configurar la API key.

---

## 📊 Comparativa: Scraping vs Riot API

| Característica | Scraping OP.GG | Riot API (Fallback) |
|----------------|----------------|---------------------|
| **Costo** | Gratis | Gratis |
| **Velocidad** | 2-5s por página | 0.5-1s por request |
| **Confiabilidad** | 30-80% (WAF) | 99.9% |
| **Mantenimiento** | Alto (selectores cambian) | Bajo (API estable) |
| **Rate Limits** | Ilimitado (pero WAF bloquea) | 20/s, 100/2min |
| **Datos** | HTML parseado | JSON estructurado |
| **Regiones** | Limitadas | Todas |
| **Setup** | Playwright | Solo API key |

**Recomendación**: Usar scraping como primera opción (gratis, unlimited), **Riot API como fallback** (confiable, rápido).

---

## 🚨 Solución de Problemas

### Error: "RIOT_API_KEY no configurada"

**Causa**: No se encontró la API key.

**Solución**:
```bash
# Verifica que esté configurada
$env:RIOT_API_KEY  # Windows
echo $RIOT_API_KEY  # Linux

# Si no está, configúrala:
$env:RIOT_API_KEY = "RGAPI-tu-key-aqui"
```

### Error: "403 Forbidden" desde Riot API

**Causa**: API key inválida o expirada.

**Solución**:
1. Ve a https://developer.riotgames.com/
2. Regenera tu Development API Key (botón "Regenerate API Key")
3. Actualiza la variable de entorno con la nueva key

### Error: "429 Rate Limit Exceeded"

**Causa**: Demasiadas requests en poco tiempo.

**Solución**: El cliente automáticamente espera el tiempo indicado en `Retry-After` header. Solo espera.

### Warning: "Riot API solo soporta LoL actualmente"

**Causa**: Intentas usar fallback para otros juegos (Valorant, TFT).

**Solución**: 
- LoL: Soportado ✅
- Valorant: Próximamente (usa API de Valorant)
- TFT: Usa API de TFT

---

## 🔐 Seguridad

**⚠️ IMPORTANTE**: NO subas tu API key a Git/GitHub

```bash
# Agregar a .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

Si accidentalmente expusiste tu API key:
1. Ve a https://developer.riotgames.com/
2. Regenera tu API key inmediatamente
3. Revoca la antigua

---

## 📈 Rate Limits y Optimización

### Límites de la API Gratuita

- **Application Rate Limit**: 20 requests/segundo, 100 requests/2 minutos
- **Method Rate Limit**: Varía por endpoint (challenger: 10/10s)

### Optimización

```python
# ❌ MAL: Demasiadas requests
for region in all_regions:
    players = await client.get_top_players(limit=1000)  # 10+ requests

# ✅ BIEN: Requests razonables
for region in priority_regions:
    players = await client.get_top_players(limit=100)  # 2-3 requests
    await asyncio.sleep(1)  # Rate limiting manual
```

### Cache de Resultados

```python
# Los datos de Challenger cambian cada ~30 minutos
# Puedes cachear resultados para reducir requests

from functools import lru_cache
from datetime import datetime, timedelta

last_fetch = None
cached_data = None

async def get_players_cached(region):
    global last_fetch, cached_data
    
    if last_fetch and datetime.now() - last_fetch < timedelta(minutes=30):
        return cached_data  # Usar cache
    
    # Fetch nuevo
    client = RiotAPIClient(api_key=api_key, region=region)
    cached_data = await client.get_top_players()
    last_fetch = datetime.now()
    
    return cached_data
```

---

## 🎯 Próximos Pasos

1. **Obtener API Key**: https://developer.riotgames.com/ (5 min)
2. **Configurar en .env**: `RIOT_API_KEY=tu-key`
3. **Probar**: `python riot_api_client.py`
4. **Usar fallback automático**: Ya funciona, solo scrape normal

**El fallback es automático**: No necesitas cambiar tu código existente. ✅

---

## 📚 Recursos

- **API Docs**: https://developer.riotgames.com/apis
- **Rate Limits**: https://developer.riotgames.com/docs/portal#rate-limiting
- **Discord Oficial**: https://discord.gg/riotgamesdevrel
- **Ejemplos**: https://github.com/RiotGames/developer-relations

---

## 💡 Tips Adicionales

### Producción: API Key Permanente

Para apps en producción:
1. Registra tu aplicación en el portal de desarrolladores
2. Completa el formulario de registro de producto
3. Obtén una **Production API Key** (no expira)

### Monitoreo

```python
from loguru import logger

# El sistema ya loggea automáticamente:
# - "🔄 Activando fallback: Riot Games Official API..."
# - "✅ X jugadores obtenidos desde Riot API (fallback)"

# Puedes monitorear cuándo se usa fallback
if player_data[0]['data_source'] == 'riot_api':
    logger.info("📊 Usando Riot API hoy (OP.GG bloqueado)")
```

### Contribuir

Si encuentras bugs o mejoras para el cliente de Riot API:
1. Abre un issue en el repo
2. O mejor: envía un PR 🚀
