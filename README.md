# GameRadar AI

**Asian Esports Intelligence Platform** — automated scouting pipeline for League of Legends, Valorant, and CS2 players across Korea, China, Japan, India, Vietnam, and SEA.

```
bronze/      ←  raw JSON scraped by GitHub Actions (11 sources)
silver/      ←  normalised, translated, scored (bronze_to_silver.py)
reports/     ←  PDF scouting reports (generate_report.py)
frontend/    ←  Next.js 14 dashboard + subscription flow
```

---

## Architecture (April 2026)

```
┌──────────────────────────────────────────────────────────────────────┐
│  GitHub Actions  (bronze_strategic.yml — every 23 h)                │
│  ingest_bronze_targets.py  →  /bronze/<source>/YYYY-MM-DD.json      │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  bronze_to_silver.py   (ETL — local or CI)                          │
│  • Reads all bronze JSON files                                       │
│  • Translates CN/JP/KO/HI/TH/VI → EN  (deep-translator)            │
│  • Calculates GameRadar Score  = KDA×0.3 + WR×0.4 + CI×0.3         │
│  • Deduplicates per (nickname, source)                               │
│  • Writes  silver/silver_data.json                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────────────┐
│  api_powerbi.py          │   │  generate_report.py                 │
│  FastAPI  :8000          │   │  Jinja2 + WeasyPrint                │
│  /export/players → BI    │   │  reports/scouting_<month>.pdf       │
└─────────────────────────┘   └─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Supabase   (Bronze/Silver/Gold tables + RLS + pgvector)            │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  frontend/   (Next.js 14)                                           │
│  Dashboard · Subscription · Payment · Discovery Hub · Semantic Srch │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```powershell
# 1. Clone and activate venv
git clone https://github.com/marcelodanieldm/gameradar.git
cd gameradar
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Copy env template
copy .env.example .env
# Edit .env → add SUPABASE_URL, SUPABASE_KEY, RIOT_API_KEY, STEAM_API_KEY

# 4. Run ETL to build silver layer
python bronze_to_silver.py --no-translate

# 5. Start Power BI API
start_api.bat           # or: uvicorn api_powerbi:app --port 8000 --reload false

# 6. Generate PDF scouting report
python generate_report.py --html-only   # preview in browser (no WeasyPrint needed)
python generate_report.py               # full PDF (requires WeasyPrint + GTK)
```

---

## Data Sources (11 active)

| Source | Region | Tech | Notes |
|---|---|---|---|
| **Dak.gg** | Korea | Playwright headless | Primary KR ladder |
| **OP.GG KR** | Korea | httpx REST | KR server stats |
| **OP.GG JP** | Japan | httpx REST | JP server stats |
| **ZETA Division** | Japan | httpx scrape | JP pro team roster |
| **DetonatioN** | Japan | httpx scrape | JP pro team roster |
| **Game-i Japan** | Japan | httpx REST | JP esports analytics |
| **Wanplus** | China | httpx REST | LPL/LDL data |
| **PentaQ** | China | httpx + proxy | Chinese stats (proxy required) |
| **The Esports Club (TEC)** | India | httpx scrape | IN competitive scene |
| **VRL Vyper** | India/SEA | httpx scrape | Valorant India/SEA |
| **GosuGamers SEA** | SEA | httpx scrape | SEA rankings |
| **Liquipedia** | Global | MediaWiki API | Backup/global coverage |
| **Riot API** | Global | REST API | Fallback for all regions |
| **Steam Web API** | Global | REST API | CS2 data |

---

## GameRadar Score Formula

$$\text{Score} = (\text{KDA}_{norm} \times 0.30) + (\text{WR}_{norm} \times 0.40) + (\text{CI}_{norm} \times 0.30)$$

- **KDA** normalized: `min(KDA, 15) / 15 × 10`  
- **WR** normalized: `WinRate% / 10`  
- **CI** (Consistency Index): derived from `consistency_score`, `games_analyzed/50`, or `tournament_participations×2`  
- Output range: **0 – 10**

---

## Key Files

### Python Pipeline

| File | Purpose |
|---|---|
| `ingest_bronze_targets.py` | Orchestrates all 11 scrapers → `/bronze/` |
| `AsiaAdapters.py` | 8 async HTTP adapters (ZETA, DetonatioN, Game-i, PentaQ, VRL Vyper, GosuGamers SEA, Liquipedia, OP.GG) |
| `StrategicAdapters.py` | `AdvancedHeaderRotator`, `ExponentialBackoffHandler`, `RegionProfile` |
| `MultiRegionIngestor.py` | Military-grade multi-region orchestrator with circuit breakers |
| `RegionalConnectors.py` | Region-specific connector extensions |
| `UniversalAggregator.py` | Enterprise data aggregation layer |
| `bronze_to_silver.py` | ETL: translate → score → deduplicate → `silver/silver_data.json` |
| `api_powerbi.py` | FastAPI on :8000 — Power BI data bridge |
| `generate_report.py` | WeasyPrint PDF scouting report renderer |
| `scrapers.py` | Base scrapers (OP.GG, Liquipedia) |
| `cnn_brasil_scraper.py` | Ninja scraper — Playwright + anti-detection |
| `riot_api_client.py` | Riot Games API v5 client |
| `proxy_rotator.py` | Rotating proxy system |
| `free_proxy_fetcher.py` | Free proxy sources |
| `country_detector.py` | Country ISO-2 detection from URLs / text |
| `models.py` | Pydantic v2 models (PlayerProfile, Stats, Champion) |
| `config.py` | Centralised configuration (pydantic-settings) |
| `pipeline.py` | Legacy: full Scraping → Bronze → Silver → Gold → Airtable |
| `skill_vector_embeddings.py` | OpenAI 4D skill vectors for pgvector similarity search |
| `embedding_generator.py` | OpenAI 1536D text embeddings |
| `payment_gateway.py` | Razorpay + Stripe integration |
| `notification_service.py` | WhatsApp / Telegram / Email alerts + PDF |
| `api_routes_sprint3.py` | Sprint 3 FastAPI routes (payments, alerts) |

### GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|---|---|---|
| `bronze_strategic.yml` | Every 23 h | Full 11-source bronze ingestion with JSON validation |
| `multi_region_ingestion.yml` | Manual / cron | MultiRegionIngestor orchestration |
| `ingest.yml` | Manual | Per-source ad-hoc ingestion |
| `ninja_scraper.yml` | Every 6 h | CNN Brasil ninja scraper |

### Frontend (Next.js 14)

```
frontend/
├── app/
│   ├── [locale]/
│   │   ├── page.tsx              # Landing page (EN, ES, EO)
│   │   ├── dashboard/page.tsx    # Protected dashboard
│   │   ├── login/page.tsx        # Auth login
│   │   └── signup/page.tsx       # Auth signup
│   └── api/
│       ├── payment/              # Razorpay / Stripe endpoints
│       ├── talent-ping/          # Notification subscriptions
│       └── semantic-search/      # OpenAI vector search
├── components/
│   ├── TransculturalDashboard.tsx   # Region-adaptive UX
│   ├── RegionalPayment.tsx          # UPI / credit card
│   ├── TalentPingSubscription.tsx   # Alert signup
│   ├── StreetScoutDashboard.tsx     # Street Scout plan UI
│   └── AISearchBar.tsx             # Semantic search UI
└── lib/
    ├── supabase/                    # Client / Server / Middleware helpers
    └── auth/                        # Auth helpers
```

---

## API Reference (`api_powerbi.py`)

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check, player count, last sync |
| `GET` | `/status` | Silver file metadata (total, sources, avg_score) |
| `POST` | `/sync?translate=false` | git pull → run ETL → reload cache |
| `GET` | `/export` | Full JSON (meta + players) |
| `GET` | `/export/players` | Flat player array — **use this in Power BI** |
| `GET` | `/export/players?region=Korea&min_score=5&limit=20` | Filtered |
| `GET` | `/export/schema` | Column documentation |
| `POST` | `/subscriber/auth` | Subscriber email verification → HMAC session token |
| `POST` | `/subscriber/preferences` | Update delivery region + language (Bearer token required) |
| `POST` | `/stripe/portal-session` | Generate Stripe billing portal URL (server-side only) |
| `POST` | `/stripe/webhook` | Stripe event handler (subscription cancellation) |

### Power BI Connection

1. Start API: `start_api.bat`
2. Power BI Desktop → Get Data → Web
3. URL: `http://127.0.0.1:8000/export/players`

Power BI row fields: `Player_Name`, `Region`, `Calculated_Score`, `Translated_Role`, `Real_Name`, `Team`, `Rank`, `Country_Code`, `Server`, `Game`, `KDA`, `Win_Rate_Pct`, `Consistency_Index`, `Games_Analyzed`, `Score_KDA_Weighted`, `Score_WinRate_Weighted`, `Score_Consistency_Weighted`, `Data_Source`, `Bronze_Date`, `Silver_Timestamp`, `Is_Partial`, `Profile_URL`, `Translations_Applied`

---

## PDF Scouting Reports (`generate_report.py`)

```powershell
# HTML preview (no GTK required)
.venv\Scripts\python.exe generate_report.py --html-only

# Full PDF
.venv\Scripts\python.exe generate_report.py

# Custom options
.venv\Scripts\python.exe generate_report.py --month "April 2026" --week 3 --top 10 --no-open
```

Output: `reports/scouting_<month>.pdf`  
Template: `templates/scouting_report.html` (dark mode, A4, Jinja2)

**WeasyPrint on Windows** requires GTK runtime:  
→ https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

---

## Subscription Plans

| Plan | Price | Searches/mo | Markets | Features |
|---|---|---|---|---|
| **Street Scout** | $9/mo | 50 | 2 | Basic ladder data |
| **Rookie** | $19/mo | 200 | 4 | + PDF scouting reports |
| **Elite Analyst** | $49/mo | Unlimited | 7 | + Real-time alerts, custom vectors |

Payment: Stripe (global) + Razorpay UPI (India — 80% of IN transactions)  
Alerts: WhatsApp · Telegram · Email

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `RIOT_API_KEY` | Yes | Riot Developer Portal API key |
| `STEAM_API_KEY` | Yes | Steam Web API key |
| `PROXY_URL` | Optional | Rotating proxy for China (PentaQ, Wanplus) |
| `WANPLUS_API_KEY` | Optional | Wanplus API key |
| `OPENAI_API_KEY` | Optional | For semantic search embeddings |
| `RAZORPAY_KEY_ID` | Optional | Razorpay payments (India) |
| `RAZORPAY_KEY_SECRET` | Optional | Razorpay secret |
| `STRIPE_SECRET_KEY` | Optional | Stripe payments (global) |
| `STRIPE_WEBHOOK_SECRET` | Optional | Stripe webhook signature verification |
| `HUB_TOKEN_SECRET` | Optional | HMAC secret for Hub session tokens (auto-generated if absent) |
| `SMTP_HOST` | Optional | Mail server for report delivery (default: smtp.gmail.com) |
| `SMTP_PORT` | Optional | SMTP port (default: 587) |
| `SMTP_USER` | Optional | Sender email login |
| `SMTP_PASSWORD` | Optional | Sender email password / app-password |
| `SMTP_FROM` | Optional | Display name + address (defaults to SMTP_USER) |
| `PORTAL_RETURN_URL` | Optional | Stripe billing portal return URL (default: http://localhost:8000) |

---

## Database Schema (Supabase / PostgreSQL)

```
bronze_raw_data          ← raw scraped records (source, timestamp, raw_json)
silver_players           ← normalised players (nickname, country, rank, kda, ...)
gold_analytics           ← promoted records + skill_vector vector(4)
subscription_plans       ← plan definitions (name, price, search_limit)
subscriptions            ← user subscriptions (user_id, plan_id, status)
subscription_usage       ← per-period search counters
payment_history          ← transaction log
search_logs              ← audit log (user_id, query, results)
```

pgvector similarity search:
```sql
SELECT * FROM search_similar_players(
    '[0.5, 0.7, 0.3, 0.8]'::vector(4),  -- [kda, winrate, aggression, versatility]
    10,                                   -- limit
    'KR',                                 -- country filter (optional)
    'LOL'                                 -- game filter (optional)
);
```

---

## Iteration History

### v0.1 — Base Foundation
`db60419` · `8a8a674`

- Bronze/Silver/Gold Supabase schema with SQL triggers
- Base scrapers: OP.GG and Liquipedia (Playwright)
- Pydantic v2 models with Unicode (CJK, Hindi, Cyrillic)
- `pipeline.py` — full orchestration (Scraping → Bronze → Silver → Gold → Airtable)
- GameRadar Score calculation function (initial)
- Next.js dashboard scaffolding

---

### v0.2 — Semantic Search & Regional UX (Sprint 2)
`94aad5c` · `c0a12c9` · `aa745ca` · `9d79827` · `bd49f05` · `ad740d0`

- **OpenAI text-embedding-ada-002** (1536D vectors) via `embedding_generator.py`
- **4D skill vectors** `[kda, winrate, aggressivity, versatility]` in `skill_vector_embeddings.py`
- `pgvector` extension + `search_similar_players()` RPC in Supabase
- `AISearchBar.tsx` — semantic search UI component
- `TransculturalDashboard.tsx` with three region modes:
  - 🇮🇳🇻🇳 India/Vietnam — mobile-first vertical feed, WhatsApp/Zalo CTA
  - 🇰🇷🇨🇳 Korea/China — dense data table, micro-metrics (APM, Gold/Min, DMG%)
  - 🇯🇵 Japan — minimalist view with metric tooltips
- Discovery Hub with culturally-differentiated modules
- Marketplace with AI-powered player recommendations
- `next-intl` i18n: English · Spanish · Esperanto landing pages
- E2E test suite (Playwright)

---

### v0.3 — Security & Authentication (Sprint 2.5)
`973ee52` · `226451a`

- Supabase Auth: email/password + email verification + JWT sessions
- `middleware.ts` — route protection, subscription checks
- Row Level Security (RLS) on all Supabase tables
- `withAuth()` / `withSubscription()` API middleware helpers
- Subscription usage tracking (searches_count, period_start/end)
- `search_logs` audit table
- `SECURITY_ANALYSIS_DASHBOARD.md` security audit

---

### v0.4 — Cashflow & Engagement (Sprint 3)
`9aeea6b` · `079b51f` · `65d0781` · `8ba105a`

- **Street Scout** plan ($9/mo): 50 searches/month, 2 markets  
  → `StreetScoutDashboard.tsx`, `payment_gateway.py` (Razorpay + Stripe)
- **Elite Analyst** plan ($49/mo): unlimited, 7 markets, custom vectors
- `TalentPingSubscription.tsx` — alert subscription UI
- `notification_service.py` — WhatsApp / Telegram / Email + PDF attachment
- `RegionalPayment.tsx` — UPI (India) + credit card (global)
- Multi-channel talent alert: Bronze trigger → notification delivery
- `api_routes_sprint3.py` — FastAPI payment + talent-ping endpoints
- Riot API automatic fallback (`demo_riot_fallback.py`)
- Free anti-WAF bypass techniques (`demo_free_bypass.py`, `free_proxy_fetcher.py`)

---

### v0.5 — Multi-Region Bronze Ingestion (Sprint 4)
`8d6792c` · `a0c66f5` · `9e6d0e4` · `dadb910` · `9c14b83` · `fb8762e`

- **11 data sources** across Korea, China, Japan, India, SEA, Global  
- `StrategicAdapters.py`:  
  - `AdvancedHeaderRotator` — per-region User-Agent + Accept-Language  
  - `ExponentialBackoffHandler` — async jitter delay  
  - `RegionProfile` enum  
- `AsiaAdapters.py` — 8 async adapters:  
  `OPGGAdapter`, `ZetaDivisionAdapter`, `DetonatioNAdapter`, `GameiJapanAdapter`,  
  `PentaQAdapter`, `VRLVyperAdapter`, `GosuGamersSEAAdapter`, `LiquipediaAdapter`  
- `ingest_bronze_targets.py` — main ingestion script, CLI `--sources --dry-run`  
- `MultiRegionIngestor.py` — military-grade orchestrator with circuit breakers  
- `RegionalConnectors.py` — region-specific connector wrappers  
- `UniversalAggregator.py` — enterprise aggregation layer  
- GitHub Actions `bronze_strategic.yml`:  
  - Cron every 23 h (`0 0 * * *` + `0 23 * * *`)  
  - 10-step job: checkout → Python 3.11 → pip cache → Playwright → scrape 11 sources → validate JSON → git commit → push  
  - `concurrency: bronze-ingest` to prevent parallel writes  
  - `workflow_dispatch` with `sources` and `dry_run` inputs  
- Bug fixes: SimpleCache `ttl` kwarg, `profile_url` in models, stderr/exit-code hygiene  

---

### v0.6 — ETL Silver Layer (Sprint 5)
`9531a11`

- **`bronze_to_silver.py`** — full ETL pipeline:  
  - Reads all `/bronze/<source>/YYYY-MM-DD.json` files (`utf-8-sig` for BOM tolerance)  
  - Translates 5 fields (`nickname`, `real_name`, `team`, `role`, `rank`) from 7 Asian languages using `GoogleTranslator`  
  - Translation cache in memory + 200 ms rate-limit delay + 5 s backoff on `TooManyRequests`  
  - Normalizes KDA (cap 15), WinRate (/10), ConsistencyIndex (from `consistency_score`, `games_analyzed`, or `tournament_participations`)  
  - Computes `score_components` breakdown (KDA×0.3, WR×0.4, CI×0.3)  
  - Deduplicates by `(nickname.lower(), _source)` — keeps highest score  
  - Writes `silver/silver_data.json` with `_meta` (record count, avg score, sources, timestamp)  
- CLI flags: `--no-translate`, `--since YYYY-MM-DD`, `--dry-run`, `--bronze-dir`, `--output`  

---

### v0.7 — Power BI API Bridge (Sprint 5 continued)
`3c25001`

- **`api_powerbi.py`** — FastAPI on fixed port 8000:  
  - `GET /export/players` — flat array in Power BI row format  
  - `POST /sync` — `git pull origin main` + runs ETL → refreshes in-memory cache  
  - `GET /status` — silver metadata (total, sources, avg_score, by_source)  
  - `GET /export/schema` — column documentation  
  - CORS enabled for localhost Power BI Desktop  
  - `reload=False` ensures port persistence across refresh cycles  
  - Source-to-Region mapping for 14 sources → Korea/China/Japan/India/SEA/Global  
- **`start_api.bat`** — double-click Windows launcher (checks .venv, shows URLs, uvicorn fallback)  

---

### v0.8 — PDF Scouting Reports (Sprint 6)
`95078a3`

- **`templates/scouting_report.html`** — 2-page A4 dark mode Jinja2 template:  
  - Palette: bg `#0f172a`, accent `#38bdf8` (cyan), A4 @ 96 dpi  
  - Page 1: logo SVG, 4 stat cards, Top 5 table with rank badges, 2 inline SVG radar charts (5 axes: KDA/WR/Consistency/Activity/Score), GameRadar Score formula block  
  - Page 2: 12-term glossary (Asian → English), full dataset table, data sources strip  
  - Jinja2 filters: `sin`, `cos`, `min` for radar geometry  
  - WeasyPrint: `print-color-adjust: exact`, `@page {size: A4; margin: 0}`  
- **`generate_report.py`** — renderer CLI:  
  - Reads `silver/silver_data.json`  
  - Builds Jinja2 context (top5, all_players, glossary, stats, data_sources)  
  - Renders HTML → WeasyPrint → `reports/scouting_<month>.pdf`  
  - `--html-only` mode (preview without GTK/WeasyPrint)  
  - Auto-opens PDF on Windows/macOS/Linux  
- Dependencies added: `weasyprint==62.3`, `jinja2==3.1.4`  

---

## Running Locally

### Bronze Ingestion (manual)
```powershell
# All 11 sources
.venv\Scripts\python.exe ingest_bronze_targets.py

# Specific sources
.venv\Scripts\python.exe ingest_bronze_targets.py --sources opgg_kr liquipedia

# Dry run (no file writes)
.venv\Scripts\python.exe ingest_bronze_targets.py --dry-run
```

### Silver ETL
```powershell
# Full translate + score
.venv\Scripts\python.exe bronze_to_silver.py

# Skip translation (faster)
.venv\Scripts\python.exe bronze_to_silver.py --no-translate

# Only files since a date
.venv\Scripts\python.exe bronze_to_silver.py --since 2026-04-01

# Dry run (no file write)
.venv\Scripts\python.exe bronze_to_silver.py --dry-run --no-translate
```

### Power BI API
```powershell
# Start API (persistent port 8000)
start_api.bat

# Or directly
.venv\Scripts\python.exe -m uvicorn api_powerbi:app --host 127.0.0.1 --port 8000

# Force sync (git pull + ETL)
curl -X POST http://127.0.0.1:8000/sync

# Query players
curl "http://127.0.0.1:8000/export/players?region=Korea&min_score=5"
```

### PDF Reports
```powershell
# HTML preview
.venv\Scripts\python.exe generate_report.py --html-only

# Full PDF
.venv\Scripts\python.exe generate_report.py

# Custom month/week
.venv\Scripts\python.exe generate_report.py --month "April 2026" --week 3
```

### GitHub Actions (manual dispatch)
```
Repository → Actions → "Bronze Ingestion — Asia Full Pipeline" → Run workflow
  sources: wanplus dakgg opgg_kr liquipedia
  dry_run: false
```

---

## Tests

```powershell
# Scraper diagnostics (connectivity tests for all 11 sources)
.venv\Scripts\python.exe test_scrapers_diagnostico.py

# MultiRegion ingestor tests
.venv\Scripts\python.exe test_multi_region_ingestor.py

# Regional connectors tests
.venv\Scripts\python.exe test_regional_connectors.py

# Universal aggregator tests
.venv\Scripts\python.exe test_universal_aggregator.py

# Ninja scraper tests
.venv\Scripts\python.exe test_ninja_scraper.py

# E2E (Playwright — requires Next.js running)
.venv\Scripts\python.exe test_e2e_playwright.py
```

---

## Known Issues

| Issue | Source | Status |
|---|---|---|
| Wanplus DNS `getaddrinfo failed` | China GFW | Works from GitHub Actions (non-CN IP) |
| PentaQ requires proxy | China | `requires_proxy=True` — skeleton fallback |
| Liquipedia rate limit ~1 req/2s | API policy | Built-in `ExponentialBackoffHandler` |
| WeasyPrint on Windows needs GTK | Windows | Use `--html-only` for preview |
| OP.GG bot detection | Korea | Playwright stealth + header rotation |

---

### v0.9 — Subscriber Lifecycle & Rookie Report Delivery (Sprint 7)
`f4d6c5c` · `cae2a37` · `ddf9e72` · `dc56d6e`

#### Cancellation lifecycle (`f4d6c5c`)
- `subscriber_sync.py` — `handle_cancellations()`: reads `cancellations_log.csv` written by webhook → marks matching rows `Inactive` in `subscribers.csv` → archives to `churn_logs.csv`
- `delivery.py` — `load_subscribers()` skips `Inactive` rows; churned users never receive a report
- `api_powerbi.py` — `POST /stripe/webhook` handles `customer.subscription.deleted`: resolves customer email via Stripe API, appends to `cancellations_log.csv`

#### Cancellation email (`cae2a37`)
- `templates/cancellation_email.html` — Jinja2 dark-mode email: access expiry date, retention offer, resubscribe CTA
- `_send_cancellation_email()` in `api_powerbi.py` — fires on webhook event; silent no-op if SMTP is unconfigured

#### Subscriber Hub v1 (`ddf9e72`)
- `frontend/hub.html` — full single-page subscriber panel (no framework, zero dependencies beyond Tailwind CDN):
  - **Current Radar card** — animated SVG radar sweep, region flag, plan meta, next report date
  - **Preferences card** — scouting region selector + report language selector
  - **Report Archive** — last 4 Mondays, download links for delivered PDFs, upcoming badges
  - Toast notification system with animation
  - `success.html` — post-payment success page now links to the Hub

#### Hub auth, preferences & Stripe billing portal (`dc56d6e`)
- `api_powerbi.py` new endpoints:
  - `POST /subscriber/auth` — validates email in `subscribers.csv` (Active only), returns HMAC-SHA256 signed token. Returns `404` for both not-found and inactive to prevent email enumeration (OWASP A07)
  - `POST /subscriber/preferences` — `Authorization: Bearer <token>` required; validates token + region/language whitelists; persists preferences atomically
  - `POST /stripe/portal-session` — server-side Stripe Customer Portal session; customer_id is **never** sent to the browser
- `_make_hub_token()` / `_verify_hub_token()` — HMAC-SHA256, TTL 86 400 s, `hmac.compare_digest` (OWASP A02)
- `_csv_safe()` — strips formula-injection characters on every write (OWASP A03)
- `hub.html` JS rewrite: `sessionStorage`-based auth (cleared on tab close), `submitAuth()`, `savePreferences()` with `Authorization: Bearer` header, `doBillingPortal()`, `renderHub()`, auth-gate overlay with fade transition

---

### v1.0 — Data Integrity & Regional Preference Delivery (Sprint 8)
`c768eff`

- **`subscriber_sync.py`** — schema extended:
  - New columns `active_region` and `target_language` added to `_CSV_FIELDNAMES`
  - `append_subscribers()` stamps `active_region = region_plan` and `target_language = "en"` on every new subscriber
  - `handle_cancellations()` back-fills both new columns for legacy rows
  - New public function **`update_preferences(email, active_region, target_language, csv_path, dry_run)`** — atomic full-rewrite under `_csv_write_lock`; validates region/language against canonical whitelists; preserves `region_plan` (billing key) untouched
- **`delivery.py`** — data-integrity rule:
  - `Subscriber` NamedTuple gains `target_language: str`
  - `load_subscribers()` reads `active_region` column — if non-empty it **overrides** `region_plan` as the effective delivery region (prevents sending an India report to someone who switched to Korea LCK in the Hub); override is logged at INFO for audit
  - Language resolution chain: `target_language` → `language` (legacy column) → `"en"`
- **`api_powerbi.py`** — `_update_subscriber_preferences()` now writes to `active_region` + `target_language` instead of `region_plan` + `language`, preserving the immutable Stripe subscription region

> **Integrity guarantee:** `active_region` is the sole source of truth for delivery; `region_plan` is the immutable billing key. They can differ after a Hub preference update.

---

### v1.1 — Hub Micro-Data Widgets (Sprint 8 continued)
`e29012e`

Three intelligence widgets added below the Preferences card in `frontend/hub.html`:

#### Market Heatmap
- Animated progress bar (CSS `cubic-bezier` transition, color-coded: green = High / amber = Medium / slate = Low)
- Per-region stat counters: tournaments detected + matches tracked this week
- Data sourced from `REGION_HEATMAP` object; auto-refreshes when the user changes region (both on save and on optimistic UI update)

#### Next Neural Report Countdown
- Live 4-cell timer: **Days · Hrs · Min · Sec** (seconds highlighted in cyan)
- Target: next Monday at 08:00 UTC; handles same-day edge case (delivery already happened vs. still pending)
- `startCountdown()` uses `setInterval(1000)` with previous interval cleanup

#### Quick API Key
- Session token displayed masked (`abc123···············ef90`) with eye-toggle reveal
- **Copy** button: `navigator.clipboard.writeText` + `document.execCommand` fallback for HTTP
- **API Docs** button: opens `{HUB_API_BASE}/docs` (FastAPI Swagger UI) in a new tab

---

### v1.2 — Hub Login / Logout (Sprint 8 continued)
`181a636`

- **Logout button** added to the sticky nav (right side, after "Manage plan" divider):
  - Mobile: icon only. `sm+`: icon + "Sign out" label. Turns red on hover.
- **`doLogout()`** function:
  1. Sets `_dirty = false` to suppress the `beforeunload` unsaved-changes dialog
  2. Stops the countdown `setInterval`
  3. Calls `_clearSession()` — wipes `sessionStorage` and in-memory `_session`
  4. Resets nav email pill to `—`
  5. Clears the login form input and hides any previous error
  6. Restores the "Access Hub →" button text/state
  7. Shows toast: `"✓ Signed out. See you next Monday."`
  8. Calls `showAuthGate()` with fade transition
- The full login → use → logout → re-login cycle is now complete

---

## Subscriber Hub — How It Works

```
Browser                          FastAPI (:8000)               subscribers.csv
  │                                     │                              │
  │  POST /subscriber/auth {email}       │                              │
  │ ──────────────────────────────────► │  lookup Active email ───────►│
  │ ◄──────────────────────────────────  │  return HMAC token           │
  │  store token in sessionStorage       │                              │
  │                                     │                              │
  │  POST /subscriber/preferences        │                              │
  │  Authorization: Bearer <token>       │                              │
  │ ──────────────────────────────────► │  verify token                │
  │                                     │  write active_region ───────►│
  │                                     │  write target_language ─────►│
  │ ◄──────────────────────────────────  │  200 OK                      │
  │                                     │                              │
  │  [Monday 08:00 UTC]                 │           delivery.py        │
  │                                     │   load_subscribers() ───────►│
  │                                     │   effective_region =         │
  │                                     │     active_region ?? region_plan
  │                                     │   send correct PDF ─────────►│
```

### Subscriber Hub API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/subscriber/auth` | — | Email lookup → HMAC token (TTL 24 h) |
| `POST` | `/subscriber/preferences` | Bearer token | Update `active_region` + `target_language` |
| `POST` | `/stripe/portal-session` | — | Server-side Stripe billing portal URL |
| `POST` | `/stripe/webhook` | Stripe signature | Handle `customer.subscription.deleted` |

### Delivery Pipeline (every Monday)

```powershell
# 1. Sync new Stripe subscribers
.venv\Scripts\python.exe subscriber_sync.py

# 2. Deliver reports (effective region = active_region ?? region_plan)
.venv\Scripts\python.exe delivery.py

# Dry run (no emails sent, no files modified)
.venv\Scripts\python.exe delivery.py --dry-run

# Single region
.venv\Scripts\python.exe delivery.py --region "Korea LCK"
```

### subscribers.csv Schema

| Column | Description |
|---|---|
| `email` | Subscriber email (lowercase) |
| `region_plan` | Original Stripe subscription region — **immutable billing key** |
| `active_region` | Current delivery region (may differ after Hub preference update) |
| `target_language` | Report language ISO 639-1 code (en / es / pt / ko / zh / ja / vi) |
| `messenger` | WhatsApp / Telegram handle (optional) |
| `plan` | Plan name (rookie) |
| `source` | stripe\_checkout |
| `subscribed_at` | ISO 8601 timestamp |
| `status` | Active \| Inactive |

---

*Repository: https://github.com/marcelodanieldm/gameradar*  
*Last updated: April 17, 2026 · HEAD `181a636`*
