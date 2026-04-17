# GameRadar AI — Index

> **Last updated:** April 2026 · HEAD `95078a3`  
> Full documentation lives in [README.md](README.md) and [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)

---

## File Tree

```
gameradar/
│
├── INGESTION
│   ├── ingest_bronze_targets.py   Entry point – 11 sources, --sources, --dry-run
│   ├── AsiaAdapters.py            8 async HTTP adapters (OP.GG KR/JP, Dak.gg, VCS, …)
│   ├── StrategicAdapters.py       Header rotation, UA spoofing, exponential backoff
│   ├── MultiRegionIngestor.py     Circuit breaker, failover, multi-source orchestrator
│   ├── RegionalConnectors.py      Region-scoped fallback connectors
│   ├── UniversalAggregator.py     Source-agnostic adapter wrapper
│   ├── scrapers.py                OP.GG / Liquipedia base scraper
│   ├── cnn_brasil_scraper.py      CNN Brasil (PT) news scraper
│   ├── proxy_rotator.py           HTTP proxy rotation helper
│   ├── free_proxy_fetcher.py      Public proxy list fetcher
│   └── bronze/                   Output: <source>/YYYY-MM-DD.json
│
├── ETL
│   └── bronze_to_silver.py       Bronze → Silver ETL, translate, score, dedupe
│
├── API
│   ├── api_powerbi.py            FastAPI :8000 – Power BI + export endpoints
│   ├── api_routes_sprint3.py     Additional Sprint 3 API routes
│   ├── start_api.bat             Windows shortcut to start Power BI API
│   └── models.py                 Pydantic v2 models
│
├── REPORTS
│   ├── generate_report.py        CLI: Jinja2 render + WeasyPrint PDF
│   ├── templates/
│   │   └── scouting_report.html  2-page A4 dark mode Jinja2 template
│   └── reports/                  Output: scouting_<month>.pdf
│
├── SILVER / GOLD
│   ├── silver/
│   │   └── silver_data.json      Current normalised dataset
│   ├── bronze_ingestion.py       Bronze Supabase uploader
│   ├── bronze_to_silver.py       (see ETL above)
│   ├── pipeline.py               Legacy orchestration pipeline
│   ├── gold_analytics.sql        Gold layer analytics queries
│   └── skill_vector_embeddings.py 4D skill vector builder
│
├── SEARCH / AI
│   ├── embedding_generator.py    OpenAI text-embedding-ada-002 (1536D)
│   ├── skill_vector_embeddings.py KDA/WR/CI/Activity → pgvector(4)
│   ├── search_similar_players_rpc.sql  pgvector RPC definition
│   ├── semantic_search_examples.py     Usage examples
│   └── country_detector.py       ISO country detection
│
├── PAYMENTS
│   └── payment_gateway.py        Stripe + Razorpay integration
│
├── NOTIFICATIONS
│   └── notification_service.py   Alert subscriptions / Talent Ping
│
├── DATABASE
│   ├── supabase_client.py        Supabase Python client wrapper
│   ├── database_schema.sql       Full schema (Bronze/Silver/Gold + subscriptions)
│   ├── ingestion_logs_schema.sql Ingestion run logs table
│   └── supabase/                 Supabase migration files
│
├── CONFIG
│   ├── config.py                 pydantic_settings – env vars
│   ├── airtable_client.py        Airtable integration
│   ├── riot_api_client.py        Riot Games API client
│   ├── ingestion_config.example.json  Source config template
│   └── players_to_ingest.example.json Player target template
│
├── TESTS
│   ├── conftest.py               pytest fixtures
│   ├── test_scrapers_diagnostico.py
│   ├── test_multi_region_ingestor.py
│   ├── test_regional_connectors.py
│   ├── test_universal_aggregator.py
│   ├── test_ninja_scraper.py
│   ├── test_e2e_playwright.py    Playwright E2E tests
│   └── debug_opgg.py             OP.GG scraper debugger
│
├── CI / CD
│   └── .github/workflows/
│       ├── bronze_strategic.yml  ← PRIMARY (every 23 h, 11 sources)
│       ├── multi_region_ingestion.yml
│       ├── run_scrapers.yml
│       └── test.yml
│
├── DOCUMENTATION
│   ├── README.md                 ← START HERE (full setup + API reference)
│   ├── ARCHITECTURE_OVERVIEW.md  Layer diagram, anti-detection, security
│   ├── INDEX.md                  This file
│   ├── COMMANDS.md               All run commands
│   ├── GITHUB_ACTIONS_SETUP.md   CI/CD secrets + workflow guide
│   ├── MULTI_REGION_INGESTOR.md  MultiRegionIngestor deep-dive
│   ├── REGIONAL_CONNECTORS.md    RegionalConnectors deep-dive
│   ├── UNIVERSAL_AGGREGATOR.md   UniversalAggregator deep-dive
│   ├── RIOT_API_GUIDE.md         Riot API setup
│   ├── TECHNICAL_REVIEW_ANTI_DETECTION.md  Anti-bot analysis
│   ├── NINJA_SCRAPER.md          Ninja scraper notes
│   ├── FREE_SOLUTIONS.md         Free-tier workarounds
│   └── OPGG_WORKAROUNDS.md       OP.GG bypass methods
│
└── FRONTEND
    └── frontend/
        ├── app/[locale]/         Next.js 14 pages (EN/ES/EO)
        │   ├── page.tsx          Landing
        │   ├── dashboard/        Protected dashboard
        │   ├── login/            Supabase auth
        │   └── signup/           Supabase auth
        ├── components/
        │   ├── TransculturalDashboard.tsx
        │   ├── RegionalPayment.tsx
        │   ├── TalentPingSubscription.tsx
        │   └── AISearchBar.tsx
        └── middleware.ts         Auth + subscription route guard
```

---

## How-To Quick Reference

| Task | Command / File |
|---|---|
| **Run bronze ingestion** | `python ingest_bronze_targets.py [--sources opgg_kr] [--dry-run]` |
| **Run silver ETL** | `python bronze_to_silver.py [--no-translate] [--since YYYY-MM-DD] [--dry-run]` |
| **Start Power BI API** | `start_api.bat` → `http://127.0.0.1:8000/export/players` |
| **Generate PDF report** | `python generate_report.py [--html-only] [--month "April 2026"]` |
| **Run all tests** | `.venv\Scripts\python.exe -m pytest tests/ -v` |
| **Run a single scraper** | `python run_working_scrapers.py` |
| **Check API status** | `curl http://127.0.0.1:8000/status` |
| **Start frontend dev** | `cd frontend && npm run dev` |

---

## Iteration History (brief)

| Version | Sprint | Key Deliverable |
|---|---|---|
| v0.1 | Sprint 1 | Base scrapers (OP.GG KR/JP), `scrapers.py`, `pipeline.py` |
| v0.2 | Sprint 2 | Semantic search, pgvector, OpenAI embeddings, i18n Next.js dashboard |
| v0.3 | Sprint 3 | Supabase Auth, RLS, subscription plans, payment gateway |
| v0.4 | Sprint 3b | Cashflow: Razorpay (India), Stripe; engagement: Talent Ping, CTAs |
| v0.5 | Sprint 4 | Multi-region bronze: 11 sources, GitHub Actions `bronze_strategic.yml` |
| v0.6 | Sprint 5 | `bronze_to_silver.py`: translation, GameRadar Score, deduplication |
| v0.7 | Sprint 6 | `api_powerbi.py`: FastAPI :8000, Power BI Direct Query bridge |
| v0.8 | Sprint 7 | `generate_report.py` + `templates/scouting_report.html`: PDF reports |

> Full details in [README.md § Iteration History](README.md).

---

*See [README.md](README.md) for environment setup, all environment variables, and contribution guide.*
