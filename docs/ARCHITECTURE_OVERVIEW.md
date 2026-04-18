# GameRadar AI — Architecture Overview

> **Last updated:** April 2026 · HEAD `95078a3`

---

## Layer Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  INGESTION  (GitHub Actions — every 23 h)                                │
│                                                                          │
│  bronze_strategic.yml                                                    │
│    └─ ingest_bronze_targets.py                                           │
│         ├─ AsiaAdapters.py        (8 async HTTP adapters)               │
│         ├─ StrategicAdapters.py   (header rotation, backoff)            │
│         ├─ MultiRegionIngestor.py (circuit breaker, failover)           │
│         └─ scrapers.py            (OP.GG, Liquipedia base)              │
│                                                                          │
│  Output: /bronze/<source>/YYYY-MM-DD.json                               │
└─────────────────────────────┬────────────────────────────────────────────┘
                              │ git commit + push
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ETL / SILVER LAYER  (local or CI)                                       │
│                                                                          │
│  bronze_to_silver.py                                                     │
│    ├─ Reads /bronze/**/*.json  (utf-8-sig, BOM-tolerant)                │
│    ├─ Translates CN/JP/KO/HI/TH/VI → EN  (deep-translator + cache)     │
│    ├─ Normalises KDA, WinRate, ConsistencyIndex  → [0, 10]              │
│    ├─ GameRadar Score = KDA×0.30 + WR×0.40 + CI×0.30                   │
│    ├─ Deduplicates by (nickname.lower(), source)                         │
│    └─ Writes silver/silver_data.json  {"_meta": …, "players": […]}      │
└─────────────────────────────┬────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────────┐   ┌─────────────────────────────────────────┐
│  API (FastAPI :8000)       │   │  REPORTS (WeasyPrint)                   │
│                           │   │                                         │
│  api_powerbi.py           │   │  generate_report.py                     │
│    GET /export/players    │   │    ├─ Reads silver_data.json            │
│    POST /sync             │   │    ├─ Renders templates/scouting_…html  │
│    GET /status            │   │    │   via Jinja2                       │
│    GET /export/schema     │   │    └─ WeasyPrint → reports/*.pdf        │
│                           │   │                                         │
│  Power BI Desktop         │   │  Rookie Plan $19/mo                     │
│    URL: /export/players   │   │  Dark mode A4, radar SVG, glossary      │
└──────────┬────────────────┘   └─────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  DATABASE (Supabase / PostgreSQL)                                        │
│                                                                          │
│  bronze_raw_data   ← raw JSON rows                                       │
│  silver_players    ← normalised players                                  │
│  gold_analytics    ← promoted + skill_vector vector(4) (pgvector)       │
│  subscriptions     ← user subscription state (RLS)                      │
│  subscription_usage ← search counters per period                        │
│  search_logs       ← audit trail                                         │
│  payment_history   ← Stripe / Razorpay transactions                     │
└──────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                                                   │
│                                                                          │
│  app/[locale]/                                                           │
│    page.tsx            ← Landing  (EN / ES / EO)                        │
│    dashboard/page.tsx  ← Protected (requires auth + subscription)       │
│    login/page.tsx      ← Supabase auth                                  │
│    signup/page.tsx     ← Supabase auth + email verification             │
│                                                                          │
│  components/                                                             │
│    TransculturalDashboard.tsx  ← Region-adaptive UX                     │
│      ├─ IndiaVietnamFeed       ← WhatsApp/Zalo CTAs, score prominent    │
│      ├─ KoreaChinaDenseTable   ← Micro-metrics, CJK fonts               │
│      └─ JapanMinimalistView    ← Tooltips, whitespace, font-light       │
│    RegionalPayment.tsx         ← UPI (India) + Stripe (global)          │
│    TalentPingSubscription.tsx  ← Alert subscription                     │
│    AISearchBar.tsx             ← pgvector semantic search               │
│                                                                          │
│  middleware.ts  ← session check → subscription check → route guard      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow (per ingestion cycle)

```
GitHub Actions (23 h cron)
  │
  ├─ python ingest_bronze_targets.py
  │     ├─ 11 adapters scrape in parallel (asyncio)
  │     ├─ Writes /bronze/<source>/YYYY-MM-DD.json
  │     └─ git commit "chore(bronze): ..."  →  git push
  │
  └─ (local trigger) python bronze_to_silver.py
        ├─ load_bronze_records()   reads all /bronze/**/*.json
        ├─ translate_record_fields()   Asian text → English
        ├─ compute_score_breakdown()   GameRadar Score
        ├─ deduplicate()
        └─ writes silver/silver_data.json
              │
              ├─ api_powerbi.py  reloads cache on GET /export
              └─ generate_report.py  renders PDF on demand
```

---

## Anti-Detection Stack

| Technique | File | Scope |
|---|---|---|
| Per-region User-Agent rotation | `StrategicAdapters.AdvancedHeaderRotator` | All HTTP sources |
| Accept-Language spoofing by region | `StrategicAdapters.RegionProfile` | KR/CN/JP/IN/SEA |
| Exponential backoff with jitter | `StrategicAdapters.ExponentialBackoffHandler` | All requests |
| Playwright stealth + `--disable-blink-features=AutomationControlled` | `ingest_bronze_targets.py` | Dak.gg, OP.GG |
| Circuit breaker (skip dead sources) | `MultiRegionIngestor` | All |
| Retry with `tenacity` (`@retry`, `stop_after_attempt(3)`) | `AsiaAdapters` | All |
| Rotating proxy | `proxy_rotator.py`, `PROXY_URL` env | PentaQ (CN) |

---

## Security Architecture

| Layer | Mechanism | Detail |
|---|---|---|
| Authentication | Supabase Auth | Email/password + email verification, JWT sessions |
| Route protection | `middleware.ts` | Checks session + active subscription before serving pages |
| API protection | `withAuth()`, `withSubscription()` | Applied to all `/api/*` routes |
| Data isolation | Row Level Security | All Supabase tables: users see only their own rows |
| Search limits | `subscription_usage` table | DB-enforced, incremented on each search |
| Audit trail | `search_logs` table | user_id, query, results_count, timestamp |
| Payment security | Stripe/Razorpay webhooks | No card data stored; transaction IDs only |
| Env secrets | GitHub Actions Secrets | SUPABASE_KEY, RIOT_API_KEY, STEAM_API_KEY, PROXY_URL |

---

## Deployment

| Component | Platform | Notes |
|---|---|---|
| Bronze ingestion | GitHub Actions (Ubuntu) | Free tier, ~15 min/run, 1,800 min/mo |
| Silver ETL | Local machine / GitHub Actions | Run after ingestion |
| Power BI API | Local machine | Port 8000, persistent |
| PDF generation | Local machine | WeasyPrint + GTK (Windows) |
| Frontend | Vercel (recommended) | `cd frontend && npm run build` |
| Database | Supabase | Managed PostgreSQL + pgvector |

---

## Key Dependencies

```
Python:
  fastapi==0.109.2        API server
  uvicorn[standard]       ASGI
  playwright==1.41.2      Headless browser scraping
  httpx==0.26.0           Async HTTP client (adapters)
  deep-translator==1.11.4 Asian language translation
  langdetect==1.0.9       Language detection
  weasyprint==62.3        HTML → PDF
  jinja2==3.1.4           Template rendering
  pydantic==2.6.1         Data validation
  loguru==0.7.2           Structured logging
  tenacity==8.2.3         Retry logic
  supabase==2.3.4         Database client
  openai==1.12.0          Embeddings (semantic search)
  razorpay==1.4.2         India payments
  stripe==8.2.0           Global payments

Frontend:
  next@14                 React framework
  @supabase/supabase-js   DB + Auth client
  next-intl               i18n (EN/ES/EO)
```

---

*See [README.md](README.md) for setup instructions, API reference, and full iteration history.*
