# 🥷 Motor de Scouting Ninja - CNN Brasil

## Descripción

Script automatizado para GitHub Actions que scrapea el Top 100 de jugadores de e-sports desde CNN Brasil, realiza upsert en Supabase con detección automática de región (India), rotación de proxies y manejo de errores silencioso.

## 🎯 Características

- ✅ **Scraping Ninja**: Rápido y eficiente con Playwright
- ✅ **Upsert automático**: Inserta o actualiza en Supabase
- ✅ **Detección de región**: Tag automático "Region: India" para jugadores indios
- ✅ **Proxy rotation**: Soporte para múltiples servicios de proxy
- ✅ **Anti-detección**: Scripts stealth para evitar bloqueos
- ✅ **Error handling silencioso**: Continúa operando sin fallar
- ✅ **GitHub Actions**: Ejecuta cada 6 horas automáticamente

## 📁 Archivos Creados

```
.github/workflows/ninja_scraper.yml  # Workflow de GitHub Actions
cnn_brasil_scraper.py                # Scraper principal
proxy_rotator.py                     # Sistema de rotación de proxies
```

## 🚀 Setup GitHub Actions

### 1. Configurar Secrets

Ve a tu repositorio → Settings → Secrets and variables → Actions

Añade los siguientes secrets:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
AIRTABLE_API_KEY=your-airtable-key (opcional)
AIRTABLE_BASE_ID=your-base-id (opcional)
AIRTABLE_TABLE_NAME=GameRadar_Players (opcional)
```

### 2. Configurar Proxies (Opcional)

Para usar proxies, añade uno de estos secrets:

**Bright Data:**
```
BRIGHT_DATA_USERNAME=your-username
BRIGHT_DATA_PASSWORD=your-password
BRIGHT_DATA_HOST=brd.superproxy.io
BRIGHT_DATA_PORT=22225
```

**ScraperAPI:**
```
SCRAPERAPI_KEY=your-api-key
```

**Custom Proxies:**
```
PROXY_LIST=host1:port1:user1:pass1,host2:port2:user2:pass2
```

### 3. Activar el Workflow

El workflow se ejecuta:
- ⏰ **Automáticamente cada 6 horas** (cron)
- 🎯 **Manualmente** desde Actions tab
- 🔄 **En cada push** a archivos relacionados

## 💻 Uso Local

### Ejecutar el scraper localmente:

```bash
# 1. Configurar .env con credenciales de Supabase
cp .env.example .env

# 2. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 3. Ejecutar scraper
python cnn_brasil_scraper.py
```

### Con proxy rotation:

```python
from cnn_brasil_scraper import CNNBrasilNinjaScraper

# Sin proxies
scraper = CNNBrasilNinjaScraper(use_proxies=False)

# Con proxies
scraper = CNNBrasilNinjaScraper(use_proxies=True)

stats = await scraper.run_ninja_scrape()
```

## 🔧 Configuración Avanzada

### Ajustar selectores CSS

Si la estructura de CNN Brasil cambia, edita los selectores en `cnn_brasil_scraper.py`:

```python
selectors = [
    "article",              # Selector genérico
    ".card",                # Cards de jugadores
    ".player-card",         # Cards específicos
    ".athlete-card",        # Athletes
    "[data-player]",        # Atributo data
]
```

### Modificar frecuencia de ejecución

Edita el cron en `.github/workflows/ninja_scraper.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Cada 6 horas
  # - cron: '0 */2 * * *'  # Cada 2 horas
  # - cron: '0 0 * * *'    # Diariamente a medianoche
```

## 📊 Output del Workflow

El workflow genera un resumen en GitHub Actions:

```
### 🥷 Ninja Scraper Results

- **Scraped**: 100 players
- **Errors**: 2
- **Duration**: 45.3s
- **Timestamp**: 2026-02-04 12:00:00 UTC
```

## 🎭 Anti-Detección

El scraper incluye múltiples técnicas anti-detección:

1. **User-Agent rotation**: Cambia entre diferentes browsers
2. **Headers reales**: Simula navegación humana
3. **WebDriver ocultado**: Elimina la propiedad navigator.webdriver
4. **Chrome runtime mock**: Simula Chrome real
5. **Delays aleatorios**: Evita patrones de bot

## 🔍 Detección de India

El sistema detecta automáticamente jugadores de India:

```python
# Detecta desde:
- Banderas emoji (🇮🇳)
- Texto "India" o "भारत"
- Servidor/región "IN"
- URL con ".in" o "/in/"

# Si se detecta India:
tags = ["Region: India"]  # Se añade automáticamente
```

## 🛡️ Error Handling Silencioso

El scraper usa "ninja mode" - nunca falla:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=False  # No reraise = silent failure
)
```

- **3 intentos automáticos** con backoff exponencial
- **Errores loggeados** pero no detienen la ejecución
- **Continue-on-error** en GitHub Actions

## 📈 Monitoreo

### Ver logs en GitHub Actions:

1. Ve a tu repo → Actions
2. Click en el workflow "Ninja E-sports Scraper"
3. Click en la ejecución más reciente
4. Expande los pasos para ver logs detallados

### Logs locales:

```bash
# Ver logs del scraper
tail -f ninja_scraper.log
```

## 🔄 Arquitectura de Datos

```
CNN Brasil E-sports
        ↓
   [Scraping con Playwright]
        ↓
   [Validación con Pydantic]
        ↓
   [Detección de País]
        ↓
   [Upsert en Supabase Bronze]
        ↓ (trigger automático)
   [Normalización a Silver]
```

## 🚨 Troubleshooting

### El scraper no encuentra jugadores:

1. Verifica que la URL está accesible
2. Revisa los selectores CSS en el código
3. Ejecuta localmente con `headless=False` para debug
4. Revisa los logs en GitHub Actions artifacts

### Problemas con proxies:

1. Verifica que las credenciales son correctas
2. Prueba sin proxies primero (`use_proxies=False`)
3. Revisa que el servicio de proxy está activo

### Errors en Supabase:

1. Verifica que los secrets están configurados
2. Confirma que el schema SQL está aplicado
3. Revisa permisos de Row Level Security

## 📝 Notas de Producción

- **Rate limiting**: El scraper respeta delays de 0.1s entre upserts
- **Timeout**: 15 minutos máximo en GitHub Actions
- **Logs**: Solo errores críticos se logguean (modo ninja)
- **Artifacts**: Los logs se guardan 7 días si hay fallos

## 🔐 Seguridad

- ✅ Secrets nunca se exponen en logs
- ✅ Logs de error no incluyen información sensible
- ✅ User agents rotativos para privacidad
- ✅ Proxies opcionales para anonimato

## 🎯 Roadmap

- [ ] Soporte para más fuentes (ESPN, The Score)
- [ ] ML para mejor extracción de datos
- [ ] Dashboard de monitoreo en tiempo real
- [ ] Notificaciones Slack/Discord
- [ ] Cache de resultados para evitar re-scraping

---

**Vibe**: Rápido, eficiente, tipo ninja 🥷
