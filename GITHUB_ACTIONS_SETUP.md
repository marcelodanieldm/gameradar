# GameRadar AI — GitHub Actions Setup

> **Last updated:** April 2026 · HEAD `95078a3`

---

## Workflows Overview

| File | Trigger | Purpose |
|---|---|---|
| `bronze_strategic.yml` | Schedule (00:00 + 23:00 UTC) + `workflow_dispatch` | **PRIMARY** — 11-source bronze ingestion |
| `multi_region_ingestion.yml` | Schedule / manual | Legacy multi-region runner |
| `run_scrapers.yml` | Manual | Quick single-source test run |
| `test.yml` | Push / PR | pytest suite |

---

## Primary Workflow: `bronze_strategic.yml`

### Schedule
- Runs at **00:00 UTC** and **23:00 UTC** daily (~23 h between cycles)
- Avoids source-site maintenance windows

### Manual trigger (`workflow_dispatch`)
```
Inputs:
  sources   (optional)  Space-separated list of sources to ingest.
                        Default: all 11
                        Options: wanplus dakgg tec_india opgg_kr opgg_jp
                                 zeta_division detonation gamei_japan
                                 pentaq vrl_vyper gosugamers_sea liquipedia

  dry_run   (optional)  false (default) | true
                        Run without writing files or committing.
```

### Manual trigger via GitHub CLI
```bash
# All sources
gh workflow run bronze_strategic.yml

# Subset of sources
gh workflow run bronze_strategic.yml -f sources="opgg_kr dak_gg liquipedia"

# Dry run
gh workflow run bronze_strategic.yml -f dry_run=true
```

### Concurrency
```yaml
concurrency:
  group: bronze-ingest
  cancel-in-progress: false  # Never cancel in-progress ingestion
```
Only one `bronze-ingest` run at a time. Queued runs wait; they are never cancelled.

### Permissions
```yaml
permissions:
  contents: write  # Required to git commit /bronze/*.json
```

### Job: `ingest`
| Step | Action |
|---|---|
| 1 | `actions/checkout@v4` — fetch repo |
| 2 | `actions/setup-python@v5` — Python 3.11 with pip cache |
| 3 | `pip install -r requirements.txt` |
| 4 | `playwright install chromium --with-deps` — for Dak.gg (React/Next.js) |
| 5 | `mkdir -p bronze/<source>` for all 11 sources |
| 6 | Smoke-test imports (`StrategicAdapters`, `AsiaAdapters`, `ingest_bronze_targets`) |
| 7 | **Run ingestion**: `python ingest_bronze_targets.py [--sources …] [--dry-run]` |
| 8 | Validate bronze JSON output |
| 9 | `git commit` + `git push` (commit message: `data(bronze): automatic ingestion <UTC date>`) |
| 10 | Upload `bronze/logs/` as artifact (retained 30 days) |

### Artifacts
Each run uploads `bronze-logs-run-<N>` to GitHub → Actions → Artifacts.

---

## Secrets Configuration

Go to **Settings → Secrets and variables → Actions → New repository secret** for each:

| Secret Name | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | `https://<project>.supabase.co` |
| `SUPABASE_KEY` | Yes | `service_role` key (not `anon`) |
| `RIOT_API_KEY` | Optional | Riot Games API key (for Valorant/LoL data) |
| `STEAM_API_KEY` | Optional | Steam Web API key |
| `PROXY_URL` | Optional | `http://user:pass@host:port` — required for PentaQ (CN) |

> **Note:** `GITHUB_TOKEN` is provided automatically by GitHub Actions — do not add it as a secret.

---

## Environment Variables in Workflow

Set in the `env:` block of the job:
```yaml
env:
  PYTHONUNBUFFERED: "1"
  PYTHONWARNINGS: "ignore:Unverified HTTPS request"
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

Optional (add as needed):
```yaml
  RIOT_API_KEY: ${{ secrets.RIOT_API_KEY }}
  STEAM_API_KEY: ${{ secrets.STEAM_API_KEY }}
  PROXY_URL: ${{ secrets.PROXY_URL }}
```

---

## Sources and Regions

| Source key | Region | Adapter | Notes |
|---|---|---|---|
| `opgg_kr` | Korea | `AsiaAdapters.OpggKrAdapter` | HTTP + header rotation |
| `opgg_jp` | Japan | `AsiaAdapters.OpggJpAdapter` | HTTP + header rotation |
| `dakgg` | Korea | `AsiaAdapters.DakggAdapter` | Playwright (React SPA) |
| `zeta_division` | Japan | `AsiaAdapters.ZetaAdapter` | HTTP |
| `detonation` | Japan | `AsiaAdapters.DetonationAdapter` | HTTP |
| `gamei_japan` | Japan | `AsiaAdapters.GameiAdapter` | HTTP |
| `wanplus` | China | `AsiaAdapters.WanplusAdapter` | DNS fails locally → works in CI |
| `pentaq` | China | `AsiaAdapters.PentaqAdapter` | Requires `PROXY_URL` |
| `tec_india` | India | `StrategicAdapters.TecIndiaAdapter` | HTTP |
| `vrl_vyper` | SEA | `StrategicAdapters.VrlAdapter` | HTTP |
| `gosugamers_sea` | SEA | `StrategicAdapters.GosuGamersAdapter` | HTTP |
| `liquipedia` | Global | `StrategicAdapters.LiquipediaAdapter` | MediaWiki API, rate-limit 1 req/2s |

---

## Other Workflows

### `multi_region_ingestion.yml`
- Legacy runner — predates 11-source pipeline
- Still functional; use `bronze_strategic.yml` for production

### `run_scrapers.yml`
- Manual trigger only
- Runs `python run_working_scrapers.py` — quick validation of base scrapers

### `test.yml`
- Triggers on `push` to `main` and on PRs
- Runs `pytest tests/ -v`
- Requires: `SUPABASE_URL`, `SUPABASE_KEY`

---

## Troubleshooting

### Wanplus DNS failure
```
getaddrinfo failed: wanplus.com
```
Symptom: Only fails locally (Windows DNS). Works from GitHub Actions (Ubuntu).  
Fix: Run ingestion from CI, or add `wanplus.com` entry to `/etc/hosts` locally.

### PentaQ empty results
Symptom: `pentaq` returns 0 records.  
Fix: Set `PROXY_URL` secret to a CN-accessible proxy.

### Playwright not found
```
Error: Browser not found. Run: playwright install chromium
```
Fix:
```powershell
.venv\Scripts\playwright.exe install chromium
```

### Rate limit on Liquipedia
Symptom: HTTP 429 after first request.  
Cause: Liquipedia enforces ~1 req/2s for anonymous clients.  
Fix: Already handled by `ExponentialBackoffHandler` in `StrategicAdapters.py`.

### Commit step skipped (no changes)
Symptom: Step 9 logs "No changes in /bronze — nothing to commit."  
Cause: All scrapers returned 0 new records (source sites may be down or rate-limiting).  
Fix: Check artifact logs, re-run with `--dry-run false` after source recovery.

### Git push permission denied
```
remote: Permission to ... denied
```
Fix: Confirm `permissions: contents: write` is set in the workflow YAML AND that the repository `GITHUB_TOKEN` permissions are not restricted under Settings → Actions → General.

---

*See [COMMANDS.md](COMMANDS.md) for local `gh` CLI trigger commands.*
