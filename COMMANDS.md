# GameRadar AI — Commands Reference

> **Last updated:** April 2026 · HEAD `95078a3`  
> All commands assume venv is activated or use the explicit `.venv\Scripts\python.exe` prefix.

---

## Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Install Playwright browser
.venv\Scripts\playwright.exe install chromium
```

---

## Bronze Ingestion

### Run all 11 sources
```powershell
.venv\Scripts\python.exe ingest_bronze_targets.py
```

### Run specific sources only
```powershell
.venv\Scripts\python.exe ingest_bronze_targets.py --sources opgg_kr opgg_jp dak_gg
```

### Dry run (no writes)
```powershell
.venv\Scripts\python.exe ingest_bronze_targets.py --dry-run
```

### Available source names
```
opgg_kr   opgg_jp   dak_gg   vcs_vn   vlr_sea   lck_site
liquipedia_lol  wanplus_cn  pentaq_cn  gamesee_in  cnn_brasil
```

### Run legacy scrapers
```powershell
.venv\Scripts\python.exe run_working_scrapers.py
.venv\Scripts\python.exe run_all_scrapers.py
.venv\Scripts\python.exe scrapers.py
```

---

## Silver ETL

### Run ETL (translate + score + dedupe)
```powershell
.venv\Scripts\python.exe bronze_to_silver.py
```

### Skip translation (faster, offline)
```powershell
.venv\Scripts\python.exe bronze_to_silver.py --no-translate
```

### Process only records after a date
```powershell
.venv\Scripts\python.exe bronze_to_silver.py --since 2026-01-01
```

### Dry run (print stats, no write)
```powershell
.venv\Scripts\python.exe bronze_to_silver.py --dry-run
```

### Custom input/output paths
```powershell
.venv\Scripts\python.exe bronze_to_silver.py --bronze-dir ./bronze --output ./silver/silver_data.json
```

---

## Power BI API

### Start the API server (Windows shortcut)
```powershell
.\start_api.bat
```

### Start manually
```powershell
.venv\Scripts\python.exe -m uvicorn api_powerbi:app --host 127.0.0.1 --port 8000
```

### API Endpoints
```powershell
# Health check
curl http://127.0.0.1:8000/

# Detailed status (loaded players, last sync)
curl http://127.0.0.1:8000/status

# Force reload from silver_data.json
curl -X POST http://127.0.0.1:8000/sync

# Export players for Power BI (JSON)
curl http://127.0.0.1:8000/export/players

# Export with filters
curl "http://127.0.0.1:8000/export/players?region=Korea&min_score=7.0&limit=50"

# Export metadata / column schema
curl http://127.0.0.1:8000/export/schema

# Export full payload (players + meta)
curl http://127.0.0.1:8000/export
```

### Power BI connection
```
1. Get Data → Web
2. URL: http://127.0.0.1:8000/export/players
3. Format: JSON
4. Transform: expand "players" list column
```

---

## PDF Reports

### Generate report for current month (PDF)
```powershell
.venv\Scripts\python.exe generate_report.py
```

### Specify output file
```powershell
.venv\Scripts\python.exe generate_report.py --output reports/april_2026.pdf
```

### Set month label and top-N players
```powershell
.venv\Scripts\python.exe generate_report.py --month "April 2026" --top 10
```

### HTML-only mode (no WeasyPrint / GTK required)
```powershell
.venv\Scripts\python.exe generate_report.py --html-only
```

### Filter by week
```powershell
.venv\Scripts\python.exe generate_report.py --week 2026-W15
```

### Generate without auto-opening result
```powershell
.venv\Scripts\python.exe generate_report.py --no-open
```

---

## Tests

### Run all tests
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Run by module
```powershell
.venv\Scripts\python.exe -m pytest test_scrapers_diagnostico.py -v
.venv\Scripts\python.exe -m pytest test_multi_region_ingestor.py -v
.venv\Scripts\python.exe -m pytest test_regional_connectors.py -v
.venv\Scripts\python.exe -m pytest test_universal_aggregator.py -v
.venv\Scripts\python.exe -m pytest test_ninja_scraper.py -v
.venv\Scripts\python.exe -m pytest test_e2e_playwright.py -v
```

### Quick smoke test (diagnostic)
```powershell
.venv\Scripts\python.exe test_scrapers_diagnostico.py
```

### Debug OP.GG scraper
```powershell
.venv\Scripts\python.exe debug_opgg.py
```

---

## Semantic Search / Embeddings

### Generate embeddings
```powershell
.venv\Scripts\python.exe embedding_generator.py
```

### Build skill vectors (4D pgvector)
```powershell
.venv\Scripts\python.exe skill_vector_embeddings.py
```

### Test semantic search
```powershell
.venv\Scripts\python.exe semantic_search_examples.py
```

---

## Database

### Push SQL schema to Supabase
```powershell
# Run in Supabase SQL Editor (dashboard.supabase.com):
#   database_schema.sql
#   ingestion_logs_schema.sql
#   gold_analytics.sql
#   search_similar_players_rpc.sql
```

---

## Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Development server
npm run dev          # http://localhost:3000

# Production build
npm run build
npm start

# Lint
npm run lint
```

---

## Git / CI

### Manual trigger for bronze ingestion workflow
```powershell
gh workflow run bronze_strategic.yml
gh workflow run bronze_strategic.yml -f sources=opgg_kr,dak_gg -f dry_run=true
```

### Check latest run
```powershell
gh run list --workflow=bronze_strategic.yml --limit 5
```

### Commit documentation changes
```powershell
git add README.md ARCHITECTURE_OVERVIEW.md INDEX.md COMMANDS.md GITHUB_ACTIONS_SETUP.md
git commit -m "docs: update documentation for all iterations"
git push origin main
```

---

*See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for secrets configuration and workflow troubleshooting.*
