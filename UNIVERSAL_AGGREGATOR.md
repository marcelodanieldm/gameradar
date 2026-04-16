# 🏗️ Universal Aggregator - Documentación

## 📋 Índice
1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Componentes Principales](#componentes-principales)
4. [Uso Básico](#uso-básico)
5. [Adapters](#adapters)
6. [Sistema de Fallback](#sistema-de-fallback)
7. [Anti-Detection](#anti-detection)
8. [Métricas y Monitoreo](#métricas-y-monitoreo)
9. [Extensibilidad](#extensibilidad)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visión General

**UniversalAggregator** es un sistema de agregación de datos que unifica múltiples fuentes de información de e-sports bajo una única interfaz. Está diseñado para:

- ✅ Escalar a **100+ fuentes de datos** sin modificar código existente
- ✅ **Fallback automático** cuando una fuente falla
- ✅ **Anti-detection** con rotación de headers y delays aleatorios
- ✅ **Circuit Breaker** para evitar bombardear fuentes caídas
- ✅ **Caché** para reducir requests duplicados
- ✅ **httpx async** para máxima velocidad
- ✅ **Métricas** detalladas por adapter

---

## 🏛️ Arquitectura

```
UniversalAggregator
├── AdapterFactory (Factory Pattern)
│   ├── RiotAPIAdapter
│   ├── OPGGAdapter
│   ├── DakGGAdapter
│   ├── TECIndiaAdapter
│   └── WanplusAdapter
├── HeaderRotator (Anti-Detection)
├── SimpleCache (TTL Cache)
├── CircuitBreaker (Resilience)
└── Metrics Tracking
```

### Patrón Adapter

Cada fuente implementa `BaseAdapter`:

```python
class BaseAdapter(ABC):
    @abstractmethod
    async def fetch_player(
        self, 
        identifier: str, 
        region: str = "global", 
        game: str = "lol"
    ) -> Optional[Dict[str, Any]]:
        pass
```

Esto permite agregar nuevas fuentes sin modificar código existente.

---

## 🧩 Componentes Principales

### 1. HeaderRotator

Rota User-Agents y headers según la región geográfica:

```python
headers = HeaderRotator.get_headers("korea")
# User-Agent: Mozilla/5.0... (Windows NT 10.0; Win64; x64; ko-KR)
# Accept-Language: ko-KR,ko;q=0.9,en;q=0.8

headers = HeaderRotator.get_headers("china")
# User-Agent: Mozilla/5.0... (zh-CN)
# Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
```

**Regiones soportadas:**
- `korea` - Headers coreanos
- `china` - Headers chinos
- `india` - Headers indios
- `global` - Headers internacionales

### 2. SimpleCache

Caché en memoria con TTL (Time To Live):

```python
cache = SimpleCache(ttl=300)  # 5 minutos

# Primera llamada - hace request
cache.get("key")  # None
cache.set("key", data)

# Segunda llamada - devuelve caché
cache.get("key")  # data

# Después de 300 segundos
cache.get("key")  # None (expiró)
```

### 3. CircuitBreaker

Evita bombardear fuentes que están fallando:

```python
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

# Simular 5 fallos
for _ in range(5):
    circuit_breaker.record_failure("opgg")

# Circuit abierto - no permite requests
circuit_breaker.is_open("opgg")  # True

# Después de 60 segundos, se permite un intento
# Si tiene éxito, el circuit se cierra
```

**Estados del Circuit:**
- `CLOSED` - Funcionando normalmente
- `OPEN` - Demasiados fallos, bloqueado
- `HALF_OPEN` - Permitiendo un intento de prueba

---

## 🚀 Uso Básico

### Ejemplo 1: Fetch Simple

```python
import asyncio
from UniversalAggregator import UniversalAggregator

async def main():
    async with UniversalAggregator() as aggregator:
        data = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["opgg"],
            region="kr"
        )
        
        print(data)
        # {
        #   "nickname": "Faker",
        #   "rank": "Challenger",
        #   "win_rate": 65.4,
        #   "source": "opgg",
        #   ...
        # }

asyncio.run(main())
```

### Ejemplo 2: Con Fallback

```python
async with UniversalAggregator() as aggregator:
    # Intentará: Riot API → OP.GG → Dak.gg
    data = await aggregator.fetch_player(
        "ShowMaker",
        preferred_sources=["riot_api", "opgg", "dakgg"],
        region="kr",
        use_fallback=True  # Activar fallback
    )
    
    print(f"Obtenido de: {data['source']}")
```

### Ejemplo 3: Batch Fetch

```python
async with UniversalAggregator() as aggregator:
    players = ["Faker", "Chovy", "ShowMaker", "Canyon", "Keria"]
    
    results = await aggregator.fetch_multiple_players(
        players,
        preferred_sources=["dakgg", "opgg"],
        max_concurrent=3,  # Máximo 3 requests paralelos
        region="kr"
    )
    
    print(f"Obtenidos: {len(results)}/{len(players)}")
```

### Ejemplo 4: Función de Alto Nivel

```python
from UniversalAggregator import fetch_player_with_fallback

# Usa configuración por defecto
data = await fetch_player_with_fallback(
    identifier="Faker",
    region="kr",
    game="lol"
)
```

---

## 🔌 Adapters

### Adapters Disponibles

| Adapter | Fuente | Región | Prioridad |
|---------|--------|--------|-----------|
| RiotAPIAdapter | Riot API oficial | Global | CRITICAL (1) |
| OPGGAdapter | OP.GG | Global, KR | HIGH (2) |
| DakGGAdapter | Dak.gg | Korea | HIGH (2) |
| TECIndiaAdapter | TEC India | India | NORMAL (3) |
| WanplusAdapter | Wanplus.com | China | NORMAL (3) |

### Crear un Nuevo Adapter

```python
from UniversalAggregator import BaseAdapter, AdapterFactory
import httpx

class LiquipediaAdapter(BaseAdapter):
    """Adapter para Liquipedia"""
    
    source_name = "liquipedia"
    
    async def fetch_player(
        self, 
        identifier: str, 
        region: str = "global", 
        game: str = "lol"
    ) -> Optional[Dict[str, Any]]:
        url = f"https://liquipedia.net/leagueoflegends/{identifier}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parsear HTML aquí
            data = self._parse_liquipedia(response.text)
            
            self._record_success()
            return data
            
        except Exception as e:
            self._record_failure()
            self.logger.error(f"Error en Liquipedia: {e}")
            return None
    
    def _parse_liquipedia(self, html: str) -> Dict[str, Any]:
        # Implementar parsing
        return {
            "nickname": "...",
            "rank": "...",
            "source": "liquipedia",
            # ...
        }

# Registrar el adapter
AdapterFactory.register(LiquipediaAdapter)
```

### Uso del Nuevo Adapter

```python
async with UniversalAggregator() as aggregator:
    data = await aggregator.fetch_player(
        "Faker",
        preferred_sources=["liquipedia"],
        region="kr"
    )
```

---

## 🔄 Sistema de Fallback

### Cómo Funciona

1. Intenta la **primera fuente** de `preferred_sources`
2. Si falla, pasa a la **segunda fuente**
3. Continúa hasta **encontrar datos** o **agotar opciones**
4. Si todas fallan, devuelve `None`

### Ejemplo de Fallback Chain

```python
# Configuración: Riot API → OP.GG → Dak.gg → TEC India → Wanplus
data = await aggregator.fetch_player(
    "indian_player_123",
    preferred_sources=["riot_api", "opgg", "dakgg", "tec_india", "wanplus"],
    use_fallback=True
)

# Logs:
# [INFO] Intentando Riot API...
# [ERROR] Riot API falló (401 Unauthorized)
# [INFO] Fallback a OP.GG...
# [ERROR] OP.GG falló (Timeout)
# [INFO] Fallback a Dak.gg...
# [ERROR] Dak.gg falló (404 Not Found)
# [INFO] Fallback a TEC India...
# [SUCCESS] Datos obtenidos de TEC India
```

### Configuración de Prioridad

```python
from UniversalAggregator import SourcePriority

# Definir orden de fuentes por región
KOREA_PRIORITY = ["dakgg", "opgg", "riot_api"]
CHINA_PRIORITY = ["wanplus", "riot_api"]
INDIA_PRIORITY = ["tec_india", "riot_api"]

# Usar en fetch
data = await aggregator.fetch_player(
    "korean_player",
    preferred_sources=KOREA_PRIORITY,
    region="kr"
)
```

---

## 🕵️ Anti-Detection

### Estrategias Implementadas

#### 1. Rotación de Headers

```python
# Headers cambian en cada request
headers1 = HeaderRotator.get_headers("korea")
headers2 = HeaderRotator.get_headers("korea")

# headers1 != headers2 (User-Agent diferente)
```

#### 2. Delays Aleatorios

```python
# China: 3-6 segundos (GFW evasion)
# Korea/India: 2-5 segundos
# Global: 1-3 segundos

await random_delay(region="china")  # Espera 3-6s
```

#### 3. httpx con HTTP/2

```python
client = httpx.AsyncClient(
    http2=True,  # Soporta HTTP/2
    limits=httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5
    ),
    timeout=httpx.Timeout(30.0)
)
```

#### 4. Circuit Breaker

Evita hacer demasiados requests a fuentes que están fallando:

```python
# Después de 5 fallos, espera 60 segundos antes de reintentar
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60
)
```

---

## 📊 Métricas y Monitoreo

### Métricas por Adapter

```python
async with UniversalAggregator() as aggregator:
    # Hacer algunos requests
    await aggregator.fetch_player("Faker", preferred_sources=["opgg"])
    await aggregator.fetch_player("Chovy", preferred_sources=["opgg"])
    
    # Obtener métricas
    metrics = aggregator.adapters["opgg"].get_metrics()
    
    print(metrics)
    # {
    #   "source": "opgg",
    #   "requests": 2,
    #   "successes": 2,
    #   "failures": 0,
    #   "success_rate": 100.0
    # }
```

### Métricas Globales

```python
metrics = aggregator.get_global_metrics()

print(metrics)
# {
#   "total_requests": 10,
#   "total_successes": 8,
#   "total_fallbacks": 2,
#   "success_rate": 80.0,
#   "adapters": [
#     {"source": "opgg", "requests": 5, "success_rate": 100.0},
#     {"source": "dakgg", "requests": 3, "success_rate": 66.7},
#     {"source": "riot_api", "requests": 2, "success_rate": 50.0}
#   ]
# }
```

### Logging Detallado

```python
from loguru import logger

# Configurar logging a archivo
logger.add(
    "aggregator_{time}.log",
    rotation="100 MB",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Logs automáticos:
# [INFO] Intentando OP.GG para jugador: Faker (region: kr)
# [SUCCESS] ✅ Datos obtenidos de OP.GG para Faker
# [INFO] Insertando en Bronze: Faker (source: opgg)
# [SUCCESS] ✅ Insertado en Bronze: Faker
```

---

## 🔧 Extensibilidad

### Agregar Nuevos Adapters (Sin Modificar Código)

1. **Crear clase del adapter:**

```python
from UniversalAggregator import BaseAdapter

class NewSourceAdapter(BaseAdapter):
    source_name = "new_source"
    
    async def fetch_player(self, identifier, region="global", game="lol"):
        # Implementación aquí
        pass
```

2. **Registrar en Factory:**

```python
from UniversalAggregator import AdapterFactory

AdapterFactory.register(NewSourceAdapter)
```

3. **Usar inmediatamente:**

```python
data = await aggregator.fetch_player(
    "player_123",
    preferred_sources=["new_source"]
)
```

### Configurar Proxies

```python
proxies = {
    "http://": "http://proxy.example.com:8080",
    "https://": "http://proxy.example.com:8080"
}

client = httpx.AsyncClient(proxies=proxies)

adapter = OPGGAdapter(
    client=client,
    cache=cache,
    circuit_breaker=circuit_breaker
)
```

### Custom Headers

```python
custom_headers = {
    "User-Agent": "MyCustomBot/1.0",
    "X-Custom-Header": "value"
}

# Sobrescribir headers por defecto
response = await client.get(url, headers=custom_headers)
```

---

## 🐛 Troubleshooting

### Problema: Todos los Adapters Fallan

**Síntomas:**
```python
data = await aggregator.fetch_player("Faker")
# None
```

**Soluciones:**

1. Verificar conectividad:
```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://www.op.gg")
    print(response.status_code)  # Debería ser 200
```

2. Revisar logs:
```python
logger.enable("UniversalAggregator")
# Mirar archivo aggregator_{time}.log
```

3. Probar adapter individual:
```python
adapter = aggregator.adapters["opgg"]
data = await adapter.fetch_player("Faker", region="kr")
```

---

### Problema: Circuit Breaker siempre abierto

**Síntomas:**
```python
circuit_breaker.is_open("opgg")  # True (siempre)
```

**Soluciones:**

1. Reducir threshold:
```python
circuit_breaker = CircuitBreaker(
    failure_threshold=10,  # Antes: 5
    timeout=30  # Antes: 60
)
```

2. Resetear manualmente:
```python
circuit_breaker.circuits["opgg"] = {
    "failures": 0,
    "status": SourceStatus.ACTIVE,
    "last_failure": None
}
```

---

### Problema: Caché no funciona

**Síntomas:**
- Múltiples requests para el mismo jugador

**Soluciones:**

1. Verificar TTL:
```python
cache = SimpleCache(ttl=600)  # 10 minutos (antes: 60)
```

2. Verificar key generation:
```python
key = cache._make_key("opgg", "Faker", "kr", "lol")
print(key)  # Debería ser hash MD5
```

3. Limpiar caché:
```python
cache.cache.clear()
```

---

### Problema: Timeout Errors

**Síntomas:**
```
httpx.ReadTimeout: Request timed out
```

**Soluciones:**

1. Aumentar timeout:
```python
client = httpx.AsyncClient(
    timeout=httpx.Timeout(60.0)  # Antes: 30.0
)
```

2. Reducir concurrencia:
```python
results = await aggregator.fetch_multiple_players(
    players,
    max_concurrent=2  # Antes: 5
)
```

---

### Problema: 403 Forbidden / Bloqueado

**Síntomas:**
```
httpx.HTTPStatusError: 403 Forbidden
```

**Soluciones:**

1. Rotar User-Agents:
```python
headers = HeaderRotator.get_headers("korea")
```

2. Usar proxies:
```python
proxies = {"http://": "http://proxy.example.com:8080"}
client = httpx.AsyncClient(proxies=proxies)
```

3. Aumentar delays:
```python
await asyncio.sleep(random.uniform(5, 10))  # 5-10 segundos
```

---

## 📈 Roadmap Futuro

### Versión 2.0
- [ ] Integración con Playwright para sitios JS-heavy
- [ ] Sistema de proxies automático (BrightData, Smartproxy)
- [ ] Machine Learning para detección de patrones de bloqueo
- [ ] Dashboard web para monitoreo en tiempo real

### Versión 3.0
- [ ] Soporte para más juegos (Dota 2, CS:GO, Valorant)
- [ ] API REST para consumo externo
- [ ] Rate limiting inteligente por fuente
- [ ] Auto-healing de adapters rotos

---

## 📚 Referencias

- [httpx Documentation](https://www.python-httpx.org/)
- [Tenacity Retry Guide](https://tenacity.readthedocs.io/)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter/python)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

---

## 🤝 Contribuciones

Para agregar un nuevo adapter:

1. Fork el repositorio
2. Crea tu adapter en `adapters/` siguiendo `BaseAdapter`
3. Agrega tests en `test_universal_aggregator.py`
4. Documenta en este archivo
5. Pull request

---

**Mantenido por:** GameRadar AI Team  
**Última actualización:** 2025-01-23  
**Versión:** 1.0.0
