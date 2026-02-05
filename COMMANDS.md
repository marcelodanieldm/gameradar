# 🎮 GameRadar AI - Comandos Útiles

## 📦 Setup Inicial

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/gameradar-ai.git
cd gameradar-ai

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright
playwright install chromium

# Copiar .env
cp .env.example .env
# Editar .env con tus credenciales
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
python test_ninja_scraper.py

# Ejecutar ejemplos
python examples.py

# Test del scraper ninja
python cnn_brasil_scraper.py
```

## 🥷 Scraper Ninja

```bash
# Ejecutar scraper (sin proxies)
python cnn_brasil_scraper.py

# Ver logs del scraper
tail -f ninja_scraper.log

# Limpiar logs
rm *.log
```

## 🗄️ Base de Datos

```bash
# Conectar a Supabase (usando psql)
# Obtener connection string de Supabase Dashboard → Settings → Database
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"

# Queries útiles
psql -c "SELECT COUNT(*) FROM bronze_raw_data WHERE source = 'cnn_brasil';"
psql -c "SELECT COUNT(*) FROM silver_players WHERE country = 'IN';"
psql -c "SELECT nickname, country, rank FROM silver_players LIMIT 10;"
```

## 📊 Pipeline Completo

```bash
# Ejecutar pipeline completo (Scraping → Bronze → Silver → Gold → Airtable)
python pipeline.py

# Ver logs del pipeline
tail -f gameradar_pipeline.log
```

## 🔍 Búsqueda y Análisis

```python
# En Python shell
from supabase_client import SupabaseClient

db = SupabaseClient()

# Top jugadores de India
players = db.get_players_by_country("IN", game="LOL", limit=10)
for p in players:
    print(f"{p['nickname']}: {p['rank']}")

# Búsqueda difusa
results = db.search_players_by_nickname_fuzzy("Faker")

# Estadísticas por región
stats = db.get_stats_by_region()
for s in stats:
    print(f"{s['country']}: {s['total_players']} jugadores")
```

## 🐛 Debugging

```bash
# Ejecutar con logs verbose
export LOG_LEVEL=DEBUG
python cnn_brasil_scraper.py

# Ver browser durante scraping (cambiar en código)
# En cnn_brasil_scraper.py:
# headless=False

# Debug de Playwright
playwright codegen https://www.cnnbrasil.com.br/esportes/outros-esportes/e-sports/

# Ver selectores disponibles
playwright show-trace trace.zip
```

## 📤 Git & GitHub

```bash
# Primer push
git add .
git commit -m "🎮 Initial commit - GameRadar AI"
git push origin main

# Push de cambios
git add .
git commit -m "🥷 Update ninja scraper"
git push

# Ver status
git status

# Ver logs
git log --oneline

# Crear nueva rama
git checkout -b feature/nueva-funcionalidad
```

## ⚙️ GitHub Actions

```bash
# Ver workflows
gh workflow list

# Ejecutar workflow manualmente
gh workflow run "🥷 Ninja E-sports Scraper"

# Ver runs
gh run list

# Ver logs de un run
gh run view [RUN_ID] --log

# Descargar artifacts
gh run download [RUN_ID]
```

## 🔐 Secrets Management

```bash
# Listar secrets (usando GitHub CLI)
gh secret list

# Añadir secret
gh secret set SUPABASE_URL

# Eliminar secret
gh secret remove OLD_SECRET
```

## 📦 Dependencias

```bash
# Actualizar todas las dependencias
pip install --upgrade -r requirements.txt

# Instalar nueva dependencia
pip install nueva-libreria
pip freeze > requirements.txt

# Ver dependencias instaladas
pip list

# Ver dependencias desactualizadas
pip list --outdated
```

## 🚀 Deployment

```bash
# Build para producción (si aplica)
python -m build

# Crear release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Ver tags
git tag -l
```

## 🧹 Limpieza

```bash
# Limpiar cache de Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Limpiar logs
rm *.log

# Limpiar build artifacts
rm -rf build/ dist/ *.egg-info/

# Limpiar todo
git clean -fdx  # ⚠️ Cuidado: elimina todo lo no trackeado
```

## 📊 Estadísticas

```bash
# Contar líneas de código
find . -name "*.py" | xargs wc -l

# Ver archivos más grandes
du -h *.py | sort -h

# Ver commits por autor
git shortlog -sn

# Ver actividad del repo
git log --since="1 week ago" --oneline
```

## 🔄 Actualización

```bash
# Actualizar desde GitHub
git pull origin main

# Reinstalar dependencias
pip install -r requirements.txt --upgrade

# Reinstalar Playwright
playwright install chromium --force
```

## 🆘 Help & Docs

```bash
# Ver ayuda de un comando
python cnn_brasil_scraper.py --help

# Ver documentación de Playwright
playwright --help

# Ver documentación de GitHub CLI
gh --help

# Abrir documentación en browser
# README: README.md
# Ninja Scraper: NINJA_SCRAPER.md
# Setup: GITHUB_SETUP.md
# Resumen: NINJA_SUMMARY.md
```

## 📝 Comandos SQL Útiles

```sql
-- Ver datos recientes de Bronze
SELECT 
    id, 
    source, 
    processing_status,
    scraped_at 
FROM bronze_raw_data 
ORDER BY scraped_at DESC 
LIMIT 10;

-- Ver jugadores de India con tag
SELECT 
    nickname,
    country,
    rank,
    raw_data->'tags' as tags
FROM bronze_raw_data 
WHERE raw_data->'tags' @> '["Region: India"]';

-- Top jugadores por win rate
SELECT 
    nickname,
    country,
    (stats->>'win_rate')::DECIMAL as win_rate,
    (stats->>'kda')::DECIMAL as kda
FROM silver_players
ORDER BY (stats->>'win_rate')::DECIMAL DESC
LIMIT 20;

-- Estadísticas por país
SELECT 
    country,
    COUNT(*) as total_players,
    AVG((stats->>'win_rate')::DECIMAL) as avg_win_rate
FROM silver_players
GROUP BY country
ORDER BY total_players DESC;

-- Ver logs de procesamiento
SELECT 
    processing_status,
    COUNT(*) as count
FROM bronze_raw_data
GROUP BY processing_status;

-- Buscar jugador por nombre (Unicode safe)
SELECT 
    nickname,
    country,
    rank
FROM silver_players
WHERE nickname ILIKE '%faker%';
```

## 🎯 Shortcuts Útiles

```bash
# Alias útiles (añadir a .bashrc o .zshrc)
alias gr='cd ~/gameradar-ai'
alias grs='python cnn_brasil_scraper.py'
alias grt='python test_ninja_scraper.py'
alias grp='python pipeline.py'
alias grl='tail -f *.log'

# Function para ver logs de GitHub Actions
ghlog() {
    gh run list --limit 1 --json databaseId --jq '.[0].databaseId' | xargs gh run view --log
}
```

## 💡 Tips

```bash
# Ejecutar en background
nohup python cnn_brasil_scraper.py > scraper.log 2>&1 &

# Programar ejecución local (cron)
# Editar crontab:
crontab -e

# Añadir línea (ejecutar cada 6 horas):
0 */6 * * * cd ~/gameradar-ai && /path/to/venv/bin/python cnn_brasil_scraper.py

# Ver trabajos programados:
crontab -l
```

---

**Pro tip**: Crea un alias para los comandos que uses frecuentemente! 🚀
