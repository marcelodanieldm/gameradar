# GameRadar AI

**Asian Esports Intelligence Platform** — automated scouting pipeline for League of Legends, Valorant, and CS2 players across Korea, China, Japan, India, Vietnam, and SEA. Delivers weekly PDF reports to subscribers every Monday via SMTP.

> **Stack:** Python 3.11 · FastAPI · Jinja2 · WeasyPrint · Stripe · pure-HTML frontend · `subscribers.csv` as data store. No Supabase. No Vercel. No Node.js. Runs 100 % locally.

```
bronze/      ←  raw JSON scraped by GitHub Actions (11 sources)
silver/      ←  normalised, translated, scored  (bronze_to_silver.py)
reports/     ←  PDF scouting reports + delivery logs
frontend/    ←  6 static HTML pages (no build step)
templates/   ←  Jinja2 HTML/CSS email + report templates
```

---

## Architecture

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
│  • Computes GameRadar Score  = KDA×0.35 + WR×0.45 + MatchFreq×0.20 │
│  • Deduplicates per (nickname, source)                               │
│  • Writes  silver/silver_data.json                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌──────────────────────────────────────┐
│  api_powerbi.py          │   │  generate_rookie_report.py           │
│  FastAPI  :8000          │   │  Jinja2 + WeasyPrint → PDF           │
│  /export/players → BI    │   │  reports/rookie_<region>_<date>.pdf  │
│  /subscriber/auth        │   └──────────────────────────────────────┘
│  /subscriber/preferences │                  │
│  /stripe/*               │                  │
└─────────────────────────┘                   │
              │                               │
              ▼                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  delivery.py  (every Monday 08:00 UTC)                              │
│  load_subscribers() → group by region → generate PDF → SMTP batch  │
│  writes reports/delivery_log_YYYY-MM-DD.csv                         │
└──────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  subscribers.csv   (sole data store)                                 │
│  email · region_plan · active_region · target_language · status     │
└──────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  frontend/   (6 static HTML files — open directly in browser)       │
│  landing.html · success.html · hub.html · unsubscribe.html · …     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```powershell
# 1. Clone and create venv
git clone https://github.com/marcelodanieldm/gameradar.git
cd gameradar
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Configure environment
copy .env.example .env
# Edit .env — minimum required keys listed in Environment Variables section

# 4. Build the silver layer (skip translation for speed)
.venv\Scripts\python.exe bronze_to_silver.py --no-translate

# 5. Start the API
start_api.bat
# → http://localhost:8000      (API)
# → http://localhost:8000/docs (Swagger UI)

# 6. Open frontend (no build step)
start frontend\landing.html
# or serve locally:
cd frontend ; python -m http.server 3000
# → http://localhost:3000/landing.html

# 7. Generate a report (HTML preview — no WeasyPrint/GTK needed)
.venv\Scripts\python.exe generate_rookie_report.py --html-only

# 8. Test delivery (no emails sent)
.venv\Scripts\python.exe delivery.py --dry-run
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

---

## GameRadar Score Formula

Score = (KDA_norm × 0.35) + (WR_norm × 0.45) + (MatchFreq_norm × 0.20) × RegionalMultiplier

- **KDA** normalized: `min(KDA, 15) / 15 × 10`
- **WR** normalized: `WinRate% / 100 × 10`
- **MatchFreq** normalized: `min(games, 150) / 150 × 10`
- **Regional multipliers:** Korea × 1.20 · India × 0.90 · others × 1.00
- Output range: **0 – 10**

---

## Key Files

### Python Pipeline

| File | Purpose |
|---|---|
| `ingest_bronze_targets.py` | Orchestrates all 11 scrapers → `/bronze/` |
| `bronze_to_silver.py` | ETL: translate → score → deduplicate → `silver/silver_data.json` |
| `data_sync.py` | Syncs and merges bronze sources into `master_rookie.json` |
| `intelligence.py` | Advanced scoring: `rank_players()` used by report generator |
| `generate_rookie_report.py` | Jinja2 + WeasyPrint → 2-page A4 PDF scouting report |
| `delivery.py` | Weekly pipeline: load subscribers → generate PDF → SMTP batch send |
| `subscriber_sync.py` | CSV read/write with threading.Lock(); `update_preferences()`, `append_subscribers()` |
| `api_powerbi.py` | FastAPI on :8000 — Power BI bridge + subscriber API + Stripe webhooks |
| `welcome_email.py` | Sends Jinja2 HTML welcome email on new subscriber registration |
| `scrapers.py` | Base scrapers (OP.GG, Liquipedia) |
| `AsiaAdapters.py` | 8 async HTTP adapters (ZETA, DetonatioN, Game-i, PentaQ, VRL, GosuGamers, Liquipedia, OP.GG) |
| `StrategicAdapters.py` | `AdvancedHeaderRotator`, `ExponentialBackoffHandler`, `RegionProfile` |
| `MultiRegionIngestor.py` | Military-grade multi-region orchestrator with circuit breakers |
| `RegionalConnectors.py` | Region-specific connector wrappers |
| `UniversalAggregator.py` | Enterprise aggregation layer |
| `cnn_brasil_scraper.py` | Ninja scraper — Playwright + anti-detection |
| `riot_api_client.py` | Riot Games API v5 client |
| `proxy_rotator.py` | Rotating proxy system |
| `free_proxy_fetcher.py` | Free proxy sources |
| `country_detector.py` | Country ISO-2 detection from URLs / text |
| `models.py` | Pydantic v2 models (PlayerProfile, Stats, Champion) |
| `config.py` | Centralised configuration (pydantic-settings) |

### Templates

| File | Purpose |
|---|---|
| `templates/rookie_report.html` | 2-page A4 dark-mode PDF report (Jinja2) |
| `templates/rookie_report.css` | Report stylesheet (print-optimised, WeasyPrint) |
| `templates/welcome_email.html` | HTML welcome email for new Rookie subscribers |
| `templates/cancellation_email.html` | HTML cancellation / access-expiry email |

### Frontend (6 static HTML files — no build step)

| File | Purpose |
|---|---|
| `frontend/landing.html` | Marketing landing page + Rookie checkout modal (EN) |
| `frontend/landing-es.html` | Landing page in Spanish |
| `frontend/landing-eo.html` | Landing page in Esperanto |
| `frontend/success.html` | Post-payment confirmation + subscriber auto-registration |
| `frontend/hub.html` | Subscriber self-service Hub (auth, preferences, widgets, archive) |
| `frontend/unsubscribe.html` | Stripe billing portal redirect + retention screen |

### GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|---|---|---|
| `bronze_strategic.yml` | Every 23 h | Full 11-source bronze ingestion with JSON validation |
| `multi_region_ingestion.yml` | Manual / cron | MultiRegionIngestor orchestration |
| `ingest.yml` | Manual | Per-source ad-hoc ingestion |
| `ninja_scraper.yml` | Every 6 h | CNN Brasil ninja scraper |

---

## Subscriber Hub

The Hub (`frontend/hub.html`) is the subscriber self-service portal — zero dependencies beyond Tailwind CDN.

```
Browser                          FastAPI (:8000)               subscribers.csv
  │  POST /subscriber/auth        │  lookup Active email ───────►│
  │ ◄── HMAC token (TTL 24 h)     │                              │
  │  store in sessionStorage       │                              │
  │                               │                              │
  │  POST /subscriber/preferences │  verify token                │
  │  Authorization: Bearer <tok>  │  write active_region ───────►│
  │                               │  write target_language ─────►│
  │                               │                              │
  │  [Monday 08:00 UTC]           │      delivery.py             │
  │                               │  effective_region =          │
  │                               │    active_region ?? region_plan
  │                               │  send correct PDF ──────────►│
```

### Hub Widgets

| Widget | Description |
|---|---|
| **Current Radar** | Animated radar SVG · region flag · plan badge · live status dot · next-Monday delivery date |
| **Scouting Settings** | Region + language selectors · POST /subscriber/preferences · unsaved-changes guard |
| **Market Heatmap** | Animated activity bar · tournament/match counts · updates on region change |
| **Next Neural Report** | Live D / H / M / S countdown to next Monday 08:00 UTC |
| **Quick API Key** | Masked token · eye-toggle · copy-to-clipboard · API Docs link |
| **Report Archive** | Last 4 Monday PDFs with DELIVERED / UPCOMING badges and download links |

### Hub API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/subscriber/auth` | — | Email lookup → HMAC-SHA256 token (TTL 24 h) |
| `POST` | `/subscriber/preferences` | Bearer token | Update `active_region` + `target_language` |
| `POST` | `/stripe/portal-session` | — | Server-side Stripe billing portal URL |
| `POST` | `/stripe/webhook` | Stripe signature | Handle `customer.subscription.deleted` |

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
| `POST` | `/subscribe` | Register new subscriber from success.html |
| `POST` | `/subscriber/auth` | Subscriber email → Hub session token |
| `POST` | `/subscriber/preferences` | Update region / language (Bearer required) |
| `POST` | `/stripe/portal-session` | Stripe billing portal URL (server-side) |
| `POST` | `/stripe/webhook` | Stripe event handler |

### Power BI Connection

```
1. start_api.bat
2. Power BI Desktop → Get Data → Web
3. URL: http://127.0.0.1:8000/export/players
```

Power BI row fields: `Player_Name`, `Region`, `Calculated_Score`, `Translated_Role`, `Real_Name`, `Team`, `Rank`, `Country_Code`, `Server`, `Game`, `KDA`, `Win_Rate_Pct`, `Consistency_Index`, `Games_Analyzed`, `Score_KDA_Weighted`, `Score_WinRate_Weighted`, `Score_Consistency_Weighted`, `Data_Source`, `Bronze_Date`, `Silver_Timestamp`, `Is_Partial`, `Profile_URL`

---

## Rookie Plan — Full Pipeline

### User Flow

```
[1] landing.html              [2] Stripe Checkout (hosted)
     Rookie CTA  ──────────►  subscription billing
     email + region modal       │
     localStorage save          │ on success
                                ▼
                          [3] success.html
                               POST /subscribe → subscribers.csv
                               webhook status badge
                               "Go to Subscriber Hub →"
                                │
                                ▼
                          [4] hub.html
                               auth gate → POST /subscriber/auth
                               ┌─ Current Radar
                               ├─ Scouting Settings
                               ├─ Market Heatmap
                               ├─ Next Neural Report countdown
                               ├─ Quick API Key
                               └─ Report Archive

[Every Monday 08:00 UTC]
   delivery.py → generate_rookie_report.py → SMTP → PDF in inbox
```

### Report Format — 2-page A4 PDF

**Page 1 — Intelligence Report**
- Header: logo · "Rookie Scouting Report" · region badge · date
- Summary stats: players ranked · region avg score · avg win rate · avg KDA
- Regional Top N table: rank medal · nickname / real name · role badge · KDA · WR · games · score bar · trend

**Page 2 — Deep Analysis**
- Rising Stars grid: top 3 cards with SVG avatar · stats row · score
- Market Trends: translated news with source badge
- Performance Radar: 5-axis SVG chart (KDA / Win Rate / Consistency / Activity / Score) — Top 1 vs Region Average

### Weekly Delivery Commands

```powershell
# Full delivery (requires SMTP env vars)
.venv\Scripts\python.exe delivery.py

# Dry run (no emails, no file writes)
.venv\Scripts\python.exe delivery.py --dry-run

# Single region only
.venv\Scripts\python.exe delivery.py --region "Korea LCK"

# Generate report without sending
.venv\Scripts\python.exe generate_rookie_report.py --region "India" --html-only
.venv\Scripts\python.exe generate_rookie_report.py --source silver --month "May 2026"
```

### subscribers.csv Schema

| Column | Description |
|---|---|
| `email` | Subscriber email (lowercase) |
| `region_plan` | Original Stripe subscription region — **immutable billing key** |
| `active_region` | Current delivery region (overrides `region_plan` when set via Hub) |
| `target_language` | Report language ISO 639-1 (`en` / `es` / `pt` / `ko` / `zh` / `ja` / `vi`) |
| `messenger` | WhatsApp / Telegram handle (optional) |
| `plan` | Plan name (`rookie`) |
| `source` | Acquisition source (`stripe_checkout`) |
| `subscribed_at` | ISO 8601 timestamp |
| `status` | `Active` \| `Inactive` |

**Data-integrity rule:** `delivery.py` uses `active_region` as the effective delivery region; falls back to `region_plan` if empty. Override is logged at INFO for audit.

---

## Running Locally

### Bronze Ingestion

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
# Full (translate + score)
.venv\Scripts\python.exe bronze_to_silver.py

# Skip translation (faster)
.venv\Scripts\python.exe bronze_to_silver.py --no-translate

# Only files since a date
.venv\Scripts\python.exe bronze_to_silver.py --since 2026-04-01

# Dry run
.venv\Scripts\python.exe bronze_to_silver.py --dry-run --no-translate
```

### Power BI API

```powershell
# Start (persistent port 8000)
start_api.bat

# Or directly
.venv\Scripts\python.exe -m uvicorn api_powerbi:app --host 127.0.0.1 --port 8000

# Force sync
curl -X POST http://127.0.0.1:8000/sync

# Query players
curl "http://127.0.0.1:8000/export/players?region=Korea&min_score=5"
```

### PDF Reports

```powershell
# HTML preview (no GTK required)
.venv\Scripts\python.exe generate_rookie_report.py --html-only

# Full PDF (requires WeasyPrint + GTK on Windows)
.venv\Scripts\python.exe generate_rookie_report.py

# Custom options
.venv\Scripts\python.exe generate_rookie_report.py --region "Korea LCK" --month "May 2026" --top 10
```

WeasyPrint on Windows requires GTK runtime:
→ https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

### GitHub Actions (manual dispatch)

```
Repository → Actions → "Bronze Ingestion — Asia Full Pipeline" → Run workflow
  sources: wanplus dakgg opgg_kr liquipedia
  dry_run: false
```

---

## Tests

```powershell
# Scraper diagnostics (connectivity for all 11 sources)
.venv\Scripts\python.exe test_scrapers_diagnostico.py

# MultiRegion ingestor
.venv\Scripts\python.exe test_multi_region_ingestor.py

# Regional connectors
.venv\Scripts\python.exe test_regional_connectors.py

# Universal aggregator
.venv\Scripts\python.exe test_universal_aggregator.py

# Ninja scraper
.venv\Scripts\python.exe test_ninja_scraper.py
```

---

## Environment Variables

### Required for the Rookie pipeline

| Variable | Description |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_…` or `sk_test_…`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_…`) |
| `HUB_TOKEN_SECRET` | Any random string ≥ 32 chars — signs Hub session tokens |
| `SMTP_USER` | Sender email login |
| `SMTP_PASSWORD` | Sender email password / app-password |

### Optional — delivery tuning

| Variable | Default | Description |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | Mail server hostname |
| `SMTP_PORT` | `587` | SMTP port (587 = STARTTLS, 465 = SSL) |
| `SMTP_FROM` | `SMTP_USER` | Sender display name + address |
| `SMTP_SSL` | `false` | Set `true` for port 465 SSL wrapper |
| `PORTAL_RETURN_URL` | `http://localhost:8000` | Stripe portal return URL |

### Optional — scraping

| Variable | Description |
|---|---|
| `RIOT_API_KEY` | Riot Developer Portal key (fallback scraper) |
| `PROXY_URL` | Rotating proxy for China sources (PentaQ, Wanplus) |
| `WANPLUS_API_KEY` | Wanplus API key |

### Minimum .env for local development

```ini
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
HUB_TOKEN_SECRET=change-this-to-any-random-32char-secret
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM=GameRadar AI <you@gmail.com>
PORTAL_RETURN_URL=http://localhost:3000/landing.html
```

---

## Subscription Plans

| Plan | Price | Reports | Markets | Features |
|---|---|---|---|---|
| **Street Scout** | $9/mo | — | 2 | Basic ladder data access |
| **Rookie** | $19/mo | Weekly PDF | 4 | AI-scored scouting report + Subscriber Hub |
| **Elite Analyst** | $49/mo | Weekly PDF | 7 | All markets + priority delivery |

Payment: Stripe (global)
Cancellation: Stripe Customer Portal → auto-marks `Inactive` in `subscribers.csv` → sends cancellation email

---

## General Features

| Feature | Description |
|---|---|
| **Zero-framework frontend** | 6 plain HTML + Tailwind CDN pages — no Node.js, no build step |
| **No database required** | `subscribers.csv` with threading.Lock() is the sole data store |
| **Region-adaptive delivery** | `active_region` overrides `region_plan` — subscribers switch region from Hub without losing billing data |
| **Multilingual reports** | `target_language` (ISO 639-1) stored per subscriber; used by delivery pipeline |
| **Stateless session** | Hub tokens in `sessionStorage` — cleared on tab close, never `localStorage` |
| **OWASP-aligned auth** | HMAC-SHA256 · `hmac.compare_digest` · 404 for both not-found and inactive (no email enumeration) |
| **CSV injection prevention** | `_csv_safe()` strips `=`, `+`, `-`, `@` from all CSV writes |
| **Delivery audit trail** | `reports/delivery_log_YYYY-MM-DD.csv` written after every Monday run |
| **PDF without a database** | Reports generated from flat JSON — works fully offline |
| **i18n landing pages** | `landing.html` (EN) · `landing-es.html` (ES) · `landing-eo.html` (EO) |
| **Dark mode throughout** | Uniform slate-950/900/800 + cyan-400/500 accent across all pages and PDFs |
| **Anti-detection scraping** | `AdvancedHeaderRotator`, `ExponentialBackoffHandler`, Playwright stealth, proxy rotation |

---

## Known Issues

| Issue | Source | Status |
|---|---|---|
| Wanplus DNS `getaddrinfo failed` | China GFW | Works from GitHub Actions (non-CN IP) |
| PentaQ requires proxy | China | `requires_proxy=True` — skeleton fallback |
| Liquipedia rate limit ~1 req/2s | API policy | Built-in `ExponentialBackoffHandler` |
| WeasyPrint on Windows needs GTK | Windows | Use `--html-only` for preview |
| OP.GG bot detection | Korea | Playwright stealth + header rotation |
| `delivery.py --dry-run` exits 1 in dev | SMTP not configured | Expected — set SMTP env vars for real runs |

---

## Iteration History

### v0.1 — Base Foundation
- Bronze/Silver/Gold Supabase schema, base scrapers, Pydantic v2 models, GameRadar Score

### v0.2 — Semantic Search & Regional UX
- OpenAI embeddings, pgvector, TransculturalDashboard, next-intl i18n (EN · ES · EO)

### v0.3 — Security & Authentication
- Supabase Auth, JWT sessions, RLS, subscription usage tracking

### v0.4 — Cashflow & Engagement
- Street Scout + Elite Analyst plans, Razorpay UPI, WhatsApp/Telegram notifications

### v0.5 — Multi-Region Bronze Ingestion
- 11 sources, `StrategicAdapters.py`, `AsiaAdapters.py`, `MultiRegionIngestor.py`, GitHub Actions every 23 h

### v0.6 — ETL Silver Layer
- `bronze_to_silver.py`: translate → score → deduplicate → `silver/silver_data.json`

### v0.7 — Power BI API Bridge
- `api_powerbi.py` FastAPI on :8000, `/export/players`, `/sync`, `start_api.bat`

### v0.8 — PDF Scouting Reports
- 2-page A4 dark-mode template, WeasyPrint, `generate_rookie_report.py`

### v0.9 — Subscriber Lifecycle & Delivery
- Stripe webhook → cancellation → Inactive in CSV → churn log
- Cancellation + welcome emails
- `delivery.py` + weekly report pipeline
- Subscriber Hub v1: HMAC auth gate, Current Radar, Preferences, Report Archive

### v1.0 — Data Integrity (Active Region)
- `active_region` + `target_language` columns in `subscribers.csv`
- `delivery.py` enforces: effective region = `active_region` ?? `region_plan`
- `subscriber_sync.update_preferences()` — atomic rewrite, whitelist validation

### v1.1 — Hub Micro-Data Widgets
- Market Heatmap (animated bar, per-region stats)
- Next Neural Report countdown (live D/H/M/S)
- Quick API Key (masked, copy, docs link)

### v1.2 — Hub Login / Logout
- Logout button in sticky nav
- `doLogout()`: clears session, stops countdown, resets form, shows auth gate

### v1.3 — Codebase Cleanup
- Removed: Supabase layer, Next.js/Vercel, Airtable, Razorpay, notification_service.py, pipeline.py, embedding_generator.py, demo scripts, npm/Node tooling
- Repository now runs 100 % locally on Python 3.11 + plain HTML

---

*Repository: https://github.com/marcelodanieldm/gameradar*
*Last updated: April 17, 2026 · HEAD `8e4d35d`*
