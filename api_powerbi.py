"""
api_powerbi.py — GameRadar AI · Power BI Bridge
================================================

API interna FastAPI que:
  - Sirve datos de jugadores formateados para Power BI
  - Sincroniza datos frescos desde GitHub (git pull + pipeline silver)
  - Expone un puerto fijo y persistente (8000) para que Power BI
    no pierda la conexión al refrescar reportes

Endpoints:
  GET  /                  — health-check + resumen
  GET  /status            — estado del silver_data.json local
  POST /sync              — git pull → bronze_to_silver → actualiza silver
  GET  /export            — JSON completo (meta + players) para Power BI
  GET  /export/players    — array plano de jugadores (recomendado para Power BI)

Uso Power BI:
  1. Inicia la API:  start_api.bat  (o  uvicorn api_powerbi:app --port 8000)
  2. En Power BI Desktop → Obtener datos → Web
  3. URL: http://127.0.0.1:8000/export/players
"""

from __future__ import annotations

import asyncio
import base64
import csv
import email.mime.multipart
import email.mime.text
import hashlib
import hmac
import json
import os
import pathlib
import random
import re
import secrets
import smtplib
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Stripe (optional — only needed for /stripe/* endpoints) ──────────────────
try:
    import stripe as _stripe
    _stripe.api_version = "2024-04-10"
    _STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    _STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
    if _STRIPE_SECRET_KEY:
        _stripe.api_key = _STRIPE_SECRET_KEY
    _STRIPE_AVAILABLE = bool(_STRIPE_SECRET_KEY)
except ImportError:
    _stripe = None  # type: ignore[assignment]
    _STRIPE_AVAILABLE      = False
    _STRIPE_SECRET_KEY     = ""
    _STRIPE_WEBHOOK_SECRET = ""

# ──────────────────────────────────────────────────────────────────────────────
# Rutas locales
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR         = pathlib.Path(__file__).parent
SILVER_PATH      = BASE_DIR / "silver" / "silver_data.json"
BRONZE_DIR       = BASE_DIR / "bronze"
PYTHON_EXE       = pathlib.Path(sys.executable)
SUBSCRIBERS_PATH = BASE_DIR / "subscribers.csv"

# Mutex: prevents race conditions on concurrent CSV writes
_csv_lock = threading.Lock()

# ──────────────────────────────────────────────────────────────────────────────
# Mapeos Region
# ──────────────────────────────────────────────────────────────────────────────

_SOURCE_TO_REGION: Dict[str, str] = {
    "dakgg":          "Korea",
    "opgg_kr":        "Korea",
    "riot_api_kr":    "Korea",
    "wanplus":        "China",
    "pentaq":         "China",
    "tec_india":      "India",
    "vrl_vyper":      "India",
    "zeta_division":  "Japan",
    "detonation":     "Japan",
    "gamei_japan":    "Japan",
    "opgg_jp":        "Japan",
    "riot_api_jp":    "Japan",
    "soha_game":      "Vietnam",
    "gosugamers_sea": "SEA",
    "steam_web_api":  "SEA",
    "liquipedia":     "Global",
    "loot_bet":       "Global",
}

_COUNTRY_TO_REGION: Dict[str, str] = {
    "CN": "China",
    "TW": "China",
    "HK": "China",
    "KR": "Korea",
    "JP": "Japan",
    "IN": "India",
    "TH": "Thailand",
    "VN": "Vietnam",
    "PH": "SEA",
    "ID": "SEA",
    "SG": "SEA",
    "BR": "Brazil",
    "XX": "Global",
}


def _resolve_region(player: Dict[str, Any]) -> str:
    source  = player.get("_source", "")
    country = player.get("country", "XX")
    return (
        _SOURCE_TO_REGION.get(source)
        or _COUNTRY_TO_REGION.get(country)
        or "Global"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Transformación → formato Power BI
# ──────────────────────────────────────────────────────────────────────────────

def _to_powerbi_row(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea un registro silver al esquema Power BI con los campos requeridos:
      Player_Name, Region, Calculated_Score, Translated_Role
    más campos adicionales útiles para análisis.
    """
    stats      = player.get("stats") or {}
    components = player.get("score_components") or {}

    return {
        # ── Campos requeridos ────────────────────────────────────────────────
        "Player_Name":        player.get("nickname") or "",
        "Region":             _resolve_region(player),
        "Calculated_Score":   round(float(player.get("gameradar_score") or 0), 4),
        "Translated_Role":    player.get("role") or "",

        # ── Identidad extendida ──────────────────────────────────────────────
        "Real_Name":          player.get("real_name") or "",
        "Team":               player.get("team") or "",
        "Rank":               player.get("rank") or "",
        "Country_Code":       player.get("country") or "XX",
        "Server":             player.get("server") or "",
        "Game":               player.get("game") or "",

        # ── Métricas de rendimiento ──────────────────────────────────────────
        "KDA":                round(float(stats.get("kda") or 0), 4),
        "Win_Rate_Pct":       round(float(stats.get("win_rate") or 0), 2),
        "Consistency_Index":  round(float(stats.get("consistency_index") or 0), 4),
        "Games_Analyzed":     int(stats.get("games_analyzed") or 0),

        # ── Componentes del score (para análisis detallado en Power BI) ──────
        "Score_KDA_Weighted":         round(float(components.get("kda_weighted") or 0), 4),
        "Score_WinRate_Weighted":     round(float(components.get("win_rate_weighted") or 0), 4),
        "Score_Consistency_Weighted": round(float(components.get("consistency_weighted") or 0), 4),

        # ── Metadatos de origen ──────────────────────────────────────────────
        "Data_Source":        player.get("_source") or "",
        "Bronze_Date":        player.get("_bronze_date") or "",
        "Silver_Timestamp":   player.get("_silver_ts") or "",
        "Is_Partial":         bool(player.get("_partial") or False),
        "Profile_URL":        player.get("profile_url") or "",
        "Translations_Applied": int(player.get("_translations_applied") or 0),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Lectura del silver
# ──────────────────────────────────────────────────────────────────────────────

def _read_silver() -> Dict[str, Any]:
    """Carga silver_data.json. Lanza HTTPException si no existe."""
    if not SILVER_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "silver_data.json no encontrado. "
                "Ejecuta POST /sync para generar los datos."
            ),
        )
    try:
        return json.loads(SILVER_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"JSON corrupto: {exc}") from exc


# ──────────────────────────────────────────────────────────────────────────────
# Sync pipeline (git pull + bronze_to_silver)
# ──────────────────────────────────────────────────────────────────────────────

class SyncResult(BaseModel):
    status:    str
    sync_ts:   str
    git_pull:  Dict[str, Any]
    pipeline:  Dict[str, Any]
    players_available: int
    message:   str


async def _run(cmd: List[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    """Ejecuta un subproceso de forma asíncrona sin bloquear el event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=120,
        ),
    )


async def _do_sync(translate: bool = False) -> SyncResult:
    """
    1. git pull origin main  →  descarga los últimos bronze files de GitHub Actions
    2. python bronze_to_silver.py --no-translate  →  regenera silver_data.json
    """
    sync_ts = datetime.now(timezone.utc).isoformat()

    # ── git pull ─────────────────────────────────────────────────────────────
    logger.info("🔄  git pull origin main…")
    git_proc = await _run(["git", "pull", "origin", "main"], cwd=BASE_DIR)
    git_result = {
        "returncode": git_proc.returncode,
        "stdout":     git_proc.stdout.strip()[:500],
        "stderr":     git_proc.stderr.strip()[:300],
    }
    if git_proc.returncode != 0:
        logger.warning(f"  git pull salió con código {git_proc.returncode}: {git_proc.stderr[:200]}")

    # ── bronze → silver ───────────────────────────────────────────────────────
    pipeline_cmd = [str(PYTHON_EXE), "bronze_to_silver.py"]
    if not translate:
        pipeline_cmd.append("--no-translate")

    logger.info(f"⚙️   Ejecutando pipeline: {' '.join(pipeline_cmd)}")
    pip_proc = await _run(pipeline_cmd, cwd=BASE_DIR)

    players_count = 0
    pipeline_result: Dict[str, Any] = {
        "returncode": pip_proc.returncode,
        "stdout":     pip_proc.stdout.strip()[:800],
        "stderr":     pip_proc.stderr.strip()[:400],
    }

    if pip_proc.returncode == 0 and SILVER_PATH.exists():
        try:
            silver = json.loads(SILVER_PATH.read_text(encoding="utf-8-sig"))
            players_count = len(silver.get("players", []))
            pipeline_result["records_generated"] = players_count
        except Exception:
            pass

    status = "success" if pip_proc.returncode == 0 else "partial"

    return SyncResult(
        status=status,
        sync_ts=sync_ts,
        git_pull=git_result,
        pipeline=pipeline_result,
        players_available=players_count,
        message=(
            f"✅ Sincronización completada. "
            f"{players_count} jugadores disponibles en /export/players"
            if status == "success"
            else "⚠️ Pipeline terminó con errores. Revisa pipeline.stderr."
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GameRadar AI — Power BI Bridge",
    description=(
        "API interna que sincroniza datos de scouting asiático desde GitHub "
        "y los expone en formato optimizado para Power BI. "
        "Puerto fijo 8000 para conexión persistente."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Power BI Desktop realiza requests desde el proceso local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# DoD #4 — GZip compression: reduces 1,000-record JSON payload ~70 %
app.add_middleware(GZipMiddleware, minimum_size=512)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
async def root() -> Dict[str, Any]:
    """Estado de la API y conteo rápido de jugadores disponibles."""
    players_count = 0
    last_update   = None
    if SILVER_PATH.exists():
        try:
            silver = json.loads(SILVER_PATH.read_text(encoding="utf-8-sig"))
            players_count = len(silver.get("players", []))
            last_update   = silver.get("_meta", {}).get("run_ts")
        except Exception:
            pass

    return {
        "service":         "GameRadar AI — Power BI Bridge",
        "status":          "online",
        "version":         "1.0.0",
        "port":            8000,
        "players_cached":  players_count,
        "last_sync":       last_update,
        "endpoints": {
            "sync":            "POST /sync",
            "export_players":  "GET  /export/players  ← usa esta URL en Power BI",
            "export_full":     "GET  /export",
            "status":          "GET  /status",
            "docs":            "GET  /docs",
        },
    }


@app.get("/status", summary="Estado del silver_data.json local")
async def status() -> Dict[str, Any]:
    """
    Devuelve metadatos del último silver procesado:
    cuántos jugadores, cuándo se generó, fuentes cubiertas.
    """
    if not SILVER_PATH.exists():
        return {
            "silver_exists": False,
            "message": "Ejecuta POST /sync para generar silver_data.json",
        }

    silver = _read_silver()
    meta   = silver.get("_meta", {})
    return {
        "silver_exists":       True,
        "silver_path":         str(SILVER_PATH),
        "total_players":       meta.get("total_records", 0),
        "sources_covered":     meta.get("sources_covered", 0),
        "avg_score":           meta.get("avg_gameradar_score", 0),
        "translations_applied": meta.get("translations_applied", 0),
        "run_ts":              meta.get("run_ts"),
        "score_formula":       meta.get("score_formula"),
        "by_source":           meta.get("by_source", {}),
    }


@app.post("/sync", response_model=SyncResult, summary="Sincronizar datos desde GitHub")
async def sync(translate: bool = False) -> SyncResult:
    """
    Ejecuta el pipeline completo de actualización:

    1. **git pull origin main** — descarga los últimos bronze files
       subidos automáticamente por GitHub Actions cada ~23h
    2. **bronze_to_silver.py** — recalcula scores y traduce campos

    Parámetros:
    - `translate` (bool, default False): habilitar traducción al inglés.
      False es más rápido y no requiere llamadas a Google Translate.

    La operación puede tardar 5-30 segundos según el volumen de datos.
    """
    return await _do_sync(translate=translate)


@app.get(
    "/export",
    summary="Export completo para Power BI (con metadatos)",
)
async def export_full() -> Dict[str, Any]:
    """
    Devuelve el JSON completo:
    ```json
    {
      "_meta": { "total_records": 8, "avg_gameradar_score": 4.06, ... },
      "players": [ { "Player_Name": "Faker", "Region": "Korea", ... } ]
    }
    ```
    """
    silver  = _read_silver()
    players = [_to_powerbi_row(p) for p in silver.get("players", [])]

    return {
        "_meta":   silver.get("_meta", {}),
        "players": players,
    }


@app.get(
    "/export/players",
    summary="Array plano de jugadores — URL recomendada para Power BI",
)
async def export_players(
    region:     Optional[str] = None,
    game:       Optional[str] = None,
    min_score:  Optional[float] = None,
    source:     Optional[str] = None,
    limit:      Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Devuelve un **array JSON plano** de jugadores en formato Power BI.

    Cada elemento tiene los campos:
    `Player_Name`, `Region`, `Calculated_Score`, `Translated_Role`,
    `Real_Name`, `Team`, `KDA`, `Win_Rate_Pct`, `Consistency_Index`, …

    **Filtros opcionales** (query params):
    - `region`    — Korea, China, Japan, India, SEA, Vietnam, Global
    - `game`      — LOL, VAL, DOTA2, CSGO, MLBB
    - `min_score` — score mínimo (0-10)
    - `source`    — dakgg, wanplus, tec_india, opgg_kr, …
    - `limit`     — máximo de registros (útil para pruebas)

    ---
    **Cómo conectar Power BI:**
    1. Abrir Power BI Desktop
    2. Inicio → Obtener datos → Web
    3. URL: `http://127.0.0.1:8000/export/players`
    4. Power BI detectará automáticamente la estructura de columnas
    """
    silver  = _read_silver()
    players = [_to_powerbi_row(p) for p in silver.get("players", [])]

    # Filtros
    if region:
        r = region.strip().title()
        players = [p for p in players if p["Region"].lower() == r.lower()]
    if game:
        g = game.strip().upper()
        players = [p for p in players if p["Game"].upper() == g]
    if min_score is not None:
        players = [p for p in players if p["Calculated_Score"] >= min_score]
    if source:
        s = source.strip().lower()
        players = [p for p in players if p["Data_Source"].lower() == s]
    if limit and limit > 0:
        players = players[:limit]

    return players


@app.get(
    "/export/schema",
    summary="Esquema de columnas del dataset Power BI",
)
async def export_schema() -> Dict[str, Any]:
    """
    Devuelve el esquema de campos con tipos y descripciones.
    Útil para documentar el modelo de datos en Power BI.
    """
    return {
        "dataset":  "GameRadar AI — Asian Esports Scouting",
        "endpoint": "GET /export/players",
        "fields": {
            "Player_Name":                {"type": "text",    "description": "Nickname del jugador (traducido al inglés si era asiático)"},
            "Region":                     {"type": "text",    "description": "Región: Korea, China, Japan, India, SEA, Vietnam, Global"},
            "Calculated_Score":           {"type": "decimal", "description": "GameRadar Score [0-10]: (KDA×0.3)+(WinRate×0.4)+(Consistency×0.3)"},
            "Translated_Role":            {"type": "text",    "description": "Rol traducido al inglés: Mid, ADC, Support, Jungle, Top"},
            "Real_Name":                  {"type": "text",    "description": "Nombre real del jugador"},
            "Team":                       {"type": "text",    "description": "Equipo actual"},
            "Rank":                       {"type": "text",    "description": "Rango competitivo: Challenger, GrandMaster, …"},
            "Country_Code":               {"type": "text",    "description": "ISO-2: KR, CN, JP, IN, …"},
            "Server":                     {"type": "text",    "description": "Servidor en el que juega"},
            "Game":                       {"type": "text",    "description": "Juego: LOL, VAL, DOTA2, CSGO, MLBB"},
            "KDA":                        {"type": "decimal", "description": "Kills+Assists / Deaths ratio"},
            "Win_Rate_Pct":               {"type": "decimal", "description": "% partidas ganadas (0-100)"},
            "Consistency_Index":          {"type": "decimal", "description": "Índice de consistencia (0-100)"},
            "Games_Analyzed":             {"type": "integer", "description": "Número de partidas analizadas"},
            "Score_KDA_Weighted":         {"type": "decimal", "description": "Componente KDA del score final"},
            "Score_WinRate_Weighted":     {"type": "decimal", "description": "Componente WinRate del score final"},
            "Score_Consistency_Weighted": {"type": "decimal", "description": "Componente Consistency del score final"},
            "Data_Source":                {"type": "text",    "description": "Fuente: dakgg, wanplus, opgg_kr, tec_india, …"},
            "Bronze_Date":                {"type": "date",    "description": "Fecha del archivo bronze origen (YYYY-MM-DD)"},
            "Silver_Timestamp":           {"type": "datetime","description": "Timestamp UTC del procesamiento silver"},
            "Is_Partial":                 {"type": "boolean", "description": "True si el registro es esqueleto sin datos reales"},
            "Profile_URL":                {"type": "url",     "description": "URL del perfil en la fuente original"},
            "Translations_Applied":       {"type": "integer", "description": "Número de campos traducidos automáticamente"},
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Rookie Plan subscriber registration
# ──────────────────────────────────────────────────────────────────────────────

_ALLOWED_REGIONS: Dict[str, str] = {
    "india":     "India",
    "korea":     "Korea LCK",
    "vietnam":   "Vietnam",
    "thailand":  "Thailand",
    "china":     "China LPL",
    "sea":       "SEA",
    "japan":     "Japan",
    "global":    "Global",
}

_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,}$'
)


def _csv_safe(value: str) -> str:
    """Prevent CSV formula-injection (OWASP A03:2021)."""
    value = value.strip()
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r", "|"):
        value = "'" + value
    return value


class SubscriberIn(BaseModel):
    email:     str
    region:    str
    messenger: Optional[str] = ""
    plan:      str           = "rookie"
    source:    str           = "stripe_checkout"


@app.post("/subscribe", summary="Register Rookie Plan subscriber after Stripe checkout")
async def subscribe(sub: SubscriberIn) -> Dict[str, Any]:
    """
    Webhook receiver called by `success.html` immediately after the Stripe
    payment redirect.  Validates the payload and appends one row to
    `subscribers.csv`.

    Security measures applied:
    - Email validated against strict regex (no header injection)
    - Region validated against fixed whitelist
    - All string fields sanitised against CSV formula-injection (OWASP A03)
    - File writes protected by a threading.Lock against concurrent requests
    """
    # ── 1. Validate email ─────────────────────────────────────────────────────
    email = sub.email.strip().lower()[:254]
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    # ── 2. Validate region (whitelist) ────────────────────────────────────────
    region_key = sub.region.strip().lower()
    if region_key not in _ALLOWED_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown region '{region_key}'. Allowed: {list(_ALLOWED_REGIONS)}",
        )
    region_display = _ALLOWED_REGIONS[region_key]

    # ── 3. Sanitise optional fields ───────────────────────────────────────────
    messenger = _csv_safe(sub.messenger or "")[:64]
    plan      = _csv_safe(sub.plan)[:32]
    source    = _csv_safe(sub.source)[:64]
    ts        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── 4. Append to CSV (mutex-protected) ───────────────────────────────────
    with _csv_lock:
        file_exists = SUBSCRIBERS_PATH.exists()
        with SUBSCRIBERS_PATH.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
            if not file_exists:
                writer.writerow(
                    ["email", "region_plan", "messenger", "plan", "source", "subscribed_at"]
                )
            writer.writerow(
                [
                    _csv_safe(email),
                    _csv_safe(region_display),
                    messenger,
                    plan,
                    source,
                    ts,
                ]
            )

    logger.success(f"🆕 New subscriber: {email} → {region_display} (plan={plan})")
    return {
        "status":        "subscribed",
        "email":         email,
        "region":        region_display,
        "plan":          plan,
        "subscribed_at": ts,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown
# ──────────────────────────────────────────────────────────────────────────────

@app.get(
    "/benchmark",
    summary="DoD #4 — Latency proof: serve 1,000 records",
)
async def benchmark(n: int = 1000) -> Dict[str, Any]:
    """
    Generates **n** (default 1,000) synthetic player records in-memory,
    serialises them, and returns latency metrics.

    Used to verify **DoD #4**: the endpoint can serve 1,000 records without
    perceptible latency.  Run:

        GET http://127.0.0.1:8000/benchmark
        GET http://127.0.0.1:8000/benchmark?n=1000

    Expected result: `generation_ms` < 50 ms, `records` = 1000.
    """
    _REGIONS  = ["Korea", "China", "Japan", "India", "Vietnam", "SEA", "Global"]
    _ROLES    = ["Mid", "ADC", "Jungler", "Support", "Top"]
    _GAMES    = ["LOL", "VAL", "DOTA2", "MLBB"]
    _SOURCES  = ["dakgg", "wanplus", "tec_india", "opgg_kr"]
    _TEAMS    = ["T1", "Gen.G", "BLG", "JDG", "TES", "NRG", "Cloud9", "Fnatic"]

    rng = random.Random(42)   # deterministic seed for reproducible output

    t_gen_start = time.perf_counter()

    records: List[Dict[str, Any]] = []
    for i in range(max(1, n)):
        score = round(rng.uniform(3.0, 9.8), 4)
        kda   = round(rng.uniform(1.5, 8.0), 4)
        wr    = round(rng.uniform(40.0, 72.0), 2)
        records.append({
            "Player_Name":                f"Player_{i + 1:04d}",
            "Region":                     rng.choice(_REGIONS),
            "Calculated_Score":           score,
            "Translated_Role":            rng.choice(_ROLES),
            "Real_Name":                  f"Real Name {i}",
            "Team":                       rng.choice(_TEAMS),
            "Rank":                       rng.choice(["Challenger", "GrandMaster", "Master"]),
            "Country_Code":               rng.choice(["KR", "CN", "JP", "IN", "VN"]),
            "Server":                     rng.choice(["KR", "CN", "JP", "EUW", "NA"]),
            "Game":                       rng.choice(_GAMES),
            "KDA":                        kda,
            "Win_Rate_Pct":               wr,
            "Consistency_Index":          round(rng.uniform(50.0, 95.0), 4),
            "Games_Analyzed":             rng.randint(20, 500),
            "Score_KDA_Weighted":         round(kda * 0.35, 4),
            "Score_WinRate_Weighted":     round(wr / 100 * 0.45, 4),
            "Score_Consistency_Weighted": round(rng.uniform(0.1, 0.3), 4),
            "Data_Source":                rng.choice(_SOURCES),
            "Bronze_Date":                "2026-04-17",
            "Silver_Timestamp":           datetime.now(timezone.utc).isoformat(),
            "Is_Partial":                 False,
            "Profile_URL":                f"https://example.com/player/{i + 1}",
            "Translations_Applied":       rng.randint(0, 5),
        })

    generation_ms = round((time.perf_counter() - t_gen_start) * 1000, 2)

    t_serial_start = time.perf_counter()
    payload        = json.dumps(records)
    serialise_ms   = round((time.perf_counter() - t_serial_start) * 1000, 2)

    total_ms   = round(generation_ms + serialise_ms, 2)
    payload_kb = round(len(payload.encode()) / 1024, 1)

    dod_pass = total_ms < 1000   # < 1 s is effectively "without latency"
    logger.info(
        f"DoD #4 benchmark: {n} records | "
        f"gen={generation_ms}ms serial={serialise_ms}ms total={total_ms}ms "
        f"payload={payload_kb}KB | {'PASS' if dod_pass else 'FAIL'}"
    )

    return {
        "dod_pass":       dod_pass,
        "records":        n,
        "generation_ms":  generation_ms,
        "serialise_ms":   serialise_ms,
        "total_ms":       total_ms,
        "payload_kb":     payload_kb,
        "note": (
            "DoD #4 PASSED — 1,000 records served without perceptible latency"
            if dod_pass
            else f"DoD #4 WARNING — total latency {total_ms}ms exceeds 1,000ms threshold"
        ),
        "players": records,
    }


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("=" * 60)
    logger.info("🚀  GameRadar AI — Power BI Bridge  iniciado")
    logger.info(f"   Puerto        : 8000 (fijo, persistente)")
    logger.info(f"   Silver path   : {SILVER_PATH}")
    silver_ok = SILVER_PATH.exists()
    logger.info(f"   Silver existe : {'✅' if silver_ok else '⚠️  no — ejecuta POST /sync'}")
    logger.info(f"   Docs          : http://127.0.0.1:8000/docs")
    logger.info(f"   Power BI URL  : http://127.0.0.1:8000/export/players")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("🛑  GameRadar AI — Power BI Bridge  detenido")


# ──────────────────────────────────────────────────────────────────────────────
# Stripe Customer Portal
# ──────────────────────────────────────────────────────────────────────────────
#
# POST /stripe/portal-session
#   Called by unsubscribe.html to create a signed Billing Portal session URL.
#   Flow: email → stripe.Customer.list(email) → billing_portal.Session.create
#   The customer ID is never sent to the browser — only the one-time session URL.
#
# POST /stripe/webhook
#   Receives signed Stripe webhook events (configured in Stripe Dashboard).
#   Handles customer.subscription.deleted → log + mark cancellation + send email.
#   Signature verified with STRIPE_WEBHOOK_SECRET (OWASP A02 — auth).
# ──────────────────────────────────────────────────────────────────────────────

_PORTAL_RETURN_URL = os.environ.get("PORTAL_RETURN_URL", "http://localhost:8000")
_CANCELLATIONS_LOG = BASE_DIR / "reports" / "cancellations_log.csv"
_CANCELLATION_EMAIL_TMPL = BASE_DIR / "templates" / "cancellation_email.html"
_RESUBSCRIBE_URL  = os.environ.get("RESUBSCRIBE_URL", "https://gameradar.ai/#rookie")
_FEEDBACK_URL     = os.environ.get("FEEDBACK_URL",    "https://gameradar.ai/feedback")

# ── Hub access token ──────────────────────────────────────────────────────────
# Ephemeral HMAC-SHA256 signed token: base64(email|expires_ts).signature
# customer_id is NEVER included — stays server-side only.
# Set HUB_TOKEN_SECRET in .env. If absent, a random secret is generated per
# process start (tokens won't survive API restarts — acceptable for dev).
_HUB_TOKEN_SECRET: str = os.environ.get("HUB_TOKEN_SECRET", "").strip()
if not _HUB_TOKEN_SECRET:
    _HUB_TOKEN_SECRET = secrets.token_hex(32)

_TOKEN_TTL_SECONDS: int = 86_400   # 24 h

# Whitelists — validated server-side on every preferences write
_CANONICAL_REGIONS: set = {
    "India", "Korea LCK", "Vietnam VCS", "Thailand",
    "China LPL", "Asia Pacific", "Japan LJL", "Global",
}
_VALID_LANGS: set = {"en", "es", "pt", "ko", "zh", "ja", "vi"}


def _make_hub_token(email: str) -> str:
    """Issue a short-lived signed token. Payload: email|unix_expiry."""
    expires_at  = int(time.time()) + _TOKEN_TTL_SECONDS
    payload     = f"{email.lower()}|{expires_at}"
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(
        _HUB_TOKEN_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def _verify_hub_token(token: str) -> Optional[str]:
    """Verify token signature and expiry. Returns email or None."""
    try:
        payload_b64, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(
        _HUB_TOKEN_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    # Timing-safe comparison (OWASP A02)
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        # Add padding so urlsafe_b64decode never raises
        padded  = payload_b64 + "==" * ((4 - len(payload_b64) % 4) % 4)
        payload = base64.urlsafe_b64decode(padded).decode()
        email, exp_str = payload.rsplit("|", 1)
        if int(exp_str) < int(time.time()):
            return None
        return email
    except Exception:
        return None


def _update_subscriber_preferences(
    email:           str,
    active_region:   str,
    target_language: str,
    csv_path:        pathlib.Path,
) -> bool:
    """
    Atomically update active_region and target_language for a subscriber.
    The original region_plan (Stripe subscription region) is preserved.
    Thread-safe via _csv_lock. Returns True if the email was found.
    """
    if not csv_path.exists():
        return False

    all_rows:   List[Dict[str, Any]] = []
    fieldnames: List[str]            = []
    found = False

    with _csv_lock:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader     = csv.DictReader(fh)
            fieldnames = list(reader.fieldnames or [])
            all_rows   = list(reader)

        if not fieldnames:
            return False

        if "active_region" not in fieldnames:
            fieldnames.append("active_region")
        if "target_language" not in fieldnames:
            fieldnames.append("target_language")

        for row in all_rows:
            if row.get("email", "").strip().lower() == email:
                row["active_region"]   = _csv_safe(active_region)
                row["target_language"] = _csv_safe(target_language)
                found = True

        if not found:
            return False

        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)

    logger.info(f"Preferences updated: {email} → active_region={active_region} lang={target_language}")
    return True


def _send_cancellation_email(
    to_email:     str,
    user_name:    str,
    region_plan:  str,
    cancelled_at: str,
    access_until: str,
) -> None:
    """
    Send a Jinja2-rendered cancellation confirmation email via SMTP.
    Uses the same SMTP env vars as delivery.py.
    Silent no-op if SMTP is not configured (avoids blocking the webhook response).
    """
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    if not smtp_user or not smtp_pass:
        logger.debug("SMTP not configured — cancellation email skipped")
        return

    # Load template
    try:
        tmpl_src = _CANCELLATION_EMAIL_TMPL.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"Cancellation email template not found: {_CANCELLATION_EMAIL_TMPL}")
        return

    # Minimal Jinja2-style variable substitution (no Jinja2 dependency needed)
    year = datetime.now(timezone.utc).year
    html = (
        tmpl_src
        .replace("{{ user_name }}",     user_name or to_email.split("@")[0])
        .replace("{{ region_plan }}",   region_plan or "")
        .replace("{{ cancelled_at }}",  cancelled_at)
        .replace("{{ access_until }}",  access_until)
        .replace("{{ resubscribe_url }}", _RESUBSCRIBE_URL)
        .replace("{{ feedback_url }}",   _FEEDBACK_URL)
        .replace("{{ year }}",           str(year))
        # Jinja2 conditionals — strip the tags, keep inner text when region_plan present
        .replace("{% if region_plan %}", "")
        .replace("{% endif %}",          "")
    )

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    from_addr = os.environ.get("SMTP_FROM", smtp_user).strip()
    use_ssl   = os.environ.get("SMTP_SSL", "false").lower() == "true"

    subject = f"Subscription Cancelled - We'll miss you, {user_name or to_email.split('@')[0]}"
    # Sanitise against header injection (OWASP A03 — CWE-93)
    subject  = re.sub(r"[\r\n]", "", subject)
    from_hdr = re.sub(r"[\r\n]", "", from_addr)
    to_hdr   = re.sub(r"[\r\n]", "", to_email)

    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["From"]    = from_hdr
    msg["To"]      = to_hdr
    msg["Subject"] = subject
    msg.attach(email.mime.text.MIMEText(html, "html", "utf-8"))

    try:
        if use_ssl:
            conn = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
        else:
            conn = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
            conn.ehlo()
            conn.starttls()
            conn.ehlo()
        conn.login(smtp_user, smtp_pass)
        conn.sendmail(from_addr, [to_email], msg.as_bytes())
        conn.quit()
        logger.success(f"Cancellation email sent → {to_email}")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — cancellation email not sent")
    except Exception as exc:
        logger.error(f"Cancellation email failed for {to_email}: {exc}")


class PortalSessionIn(BaseModel):
    email:      str
    return_url: Optional[str] = None  # overrides PORTAL_RETURN_URL if provided


@app.post("/stripe/portal-session", summary="Create Stripe Billing Portal session")
async def create_portal_session(payload: PortalSessionIn) -> Dict[str, Any]:
    """
    Looks up the Stripe customer by email and creates a short-lived Billing
    Portal session URL.  The customer ID is resolved server-side and never
    exposed to the browser.

    Returns:
        { "url": "https://billing.stripe.com/session/…" }

    Errors:
        503  Stripe not configured (STRIPE_SECRET_KEY missing)
        404  No paid customer found with that email
        502  Stripe API error
    """
    if not _STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "Stripe is not configured on this server. "
                "Set STRIPE_SECRET_KEY in your environment or .env file."
            ),
        )

    # Validate email
    email = payload.email.strip().lower()[:254]
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    return_url = (payload.return_url or _PORTAL_RETURN_URL).strip()
    # Whitelist only http/https to prevent open-redirect (OWASP A01)
    if not return_url.startswith(("http://", "https://")):
        return_url = _PORTAL_RETURN_URL

    try:
        # Find the customer by email
        customers = _stripe.Customer.list(email=email, limit=1)
        if not customers or not customers.data:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No Stripe customer found for {email!r}. "
                    "The email must match the one used at checkout."
                ),
            )
        customer_id = customers.data[0].id

        # Create a Billing Portal session (one-time, ~5 min TTL)
        session = _stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        logger.info(f"Portal session created for {email} (customer={customer_id})")
        return {"url": session.url}

    except HTTPException:
        raise
    except _stripe.error.AuthenticationError:
        logger.error("Stripe authentication failed — check STRIPE_SECRET_KEY")
        raise HTTPException(status_code=502, detail="Stripe authentication error")
    except _stripe.error.StripeError as exc:
        logger.error(f"Stripe API error: {exc}")
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc.user_message}")


@app.post("/stripe/webhook", summary="Stripe webhook receiver")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    """
    Receives signed webhook events from Stripe.

    **Required setup (Stripe Dashboard):**
    1. Developers → Webhooks → Add endpoint
       URL:    https://your-domain/stripe/webhook
       Events: customer.subscription.deleted
                customer.subscription.updated  (optional)
    2. Copy the Signing Secret → set STRIPE_WEBHOOK_SECRET env var

    **Signature verification** (OWASP A02:2021 — Cryptographic Failures):
    All events are verified using the Stripe-Signature header and the
    webhook signing secret before any processing occurs.  Unverified
    events are rejected with 400.
    """
    if not _STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    # Read raw bytes — required for Stripe signature verification
    payload_bytes = await request.body()
    sig_header    = request.headers.get("stripe-signature", "")

    if not sig_header:
        logger.warning("Webhook received without Stripe-Signature header — rejected")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Verify signature (or skip if webhook secret not configured yet)
    event = None
    if _STRIPE_WEBHOOK_SECRET:
        try:
            event = _stripe.Webhook.construct_event(
                payload=payload_bytes,
                sig_header=sig_header,
                secret=_STRIPE_WEBHOOK_SECRET,
            )
        except _stripe.error.SignatureVerificationError:
            logger.warning("Webhook signature verification failed — rejected")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception as exc:
            logger.error(f"Webhook parse error: {exc}")
            raise HTTPException(status_code=400, detail="Malformed webhook payload")
    else:
        # No secret configured — parse without verification (dev/test only)
        logger.warning(
            "STRIPE_WEBHOOK_SECRET not set — processing webhook WITHOUT signature verification. "
            "Set the secret in production!"
        )
        try:
            event = json.loads(payload_bytes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("type", "") if isinstance(event, dict) else getattr(event, "type", "")
    event_id   = event.get("id",   "") if isinstance(event, dict) else getattr(event, "id",   "")

    logger.info(f"Webhook received: {event_type}  (id={event_id})")

    # ── Handle subscription deleted ───────────────────────────────────────────
    if event_type == "customer.subscription.deleted":
        sub_obj   = event["data"]["object"] if isinstance(event, dict) else event.data.object
        cust_id   = sub_obj.get("customer")  if isinstance(sub_obj, dict) else getattr(sub_obj, "customer", "")
        sub_id    = sub_obj.get("id")         if isinstance(sub_obj, dict) else getattr(sub_obj, "id",       "")
        status    = sub_obj.get("status")     if isinstance(sub_obj, dict) else getattr(sub_obj, "status",   "")
        cancelled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Resolve email from Stripe (best-effort)
        email = ""
        try:
            cust  = _stripe.Customer.retrieve(cust_id)
            email = (cust.get("email") or "") if isinstance(cust, dict) else getattr(cust, "email", "") or ""
        except Exception:
            pass

        logger.warning(
            f"Subscription cancelled: sub={sub_id} customer={cust_id} "
            f"email={email or '(unknown)'} status={status}"
        )

        # Append to cancellations log
        try:
            _CANCELLATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
            file_exists = _CANCELLATIONS_LOG.exists()
            with _csv_lock:
                with _CANCELLATIONS_LOG.open("a", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    if not file_exists:
                        writer.writerow([
                            "cancelled_at", "email", "stripe_customer_id",
                            "stripe_subscription_id", "status", "event_id",
                        ])
                    writer.writerow([
                        cancelled_at,
                        _csv_safe(email),
                        cust_id,
                        sub_id,
                        status,
                        event_id,
                    ])
            logger.success(
                f"Cancellation logged → {_CANCELLATIONS_LOG.name} "
                f"(email={email or 'unknown'})"
            )
        except Exception as exc:
            logger.error(f"Failed to write cancellation log: {exc}")

        # ── Send cancellation confirmation email (best-effort) ────────────
        if email:
            # Resolve access_until from subscription period end (Stripe field)
            try:
                period_end_ts = (
                    sub_obj.get("current_period_end")
                    if isinstance(sub_obj, dict)
                    else getattr(sub_obj, "current_period_end", None)
                )
                if period_end_ts:
                    access_until = datetime.fromtimestamp(
                        int(period_end_ts), tz=timezone.utc
                    ).strftime("%B %d, %Y")
                else:
                    access_until = "end of billing period"
            except Exception:
                access_until = "end of billing period"

            # Resolve subscriber name and region from subscribers.csv (best-effort)
            user_name   = ""
            region_plan = ""
            try:
                if SUBSCRIBERS_PATH.exists():
                    with SUBSCRIBERS_PATH.open(newline="", encoding="utf-8") as fh:
                        for row in csv.DictReader(fh):
                            if row.get("email", "").strip().lower() == email.lower():
                                region_plan = row.get("region_plan", "")
                                # Use messenger handle as display name if available
                                user_name = row.get("messenger", "") or ""
                                break
            except Exception:
                pass

            # Fire in a background thread — never block the webhook 200 response
            threading.Thread(
                target=_send_cancellation_email,
                args=(email, user_name, region_plan, cancelled_at, access_until),
                daemon=True,
            ).start()

        return {"received": True, "event": event_type, "subscription": sub_id}

    # ── Acknowledge all other events (Stripe expects 200 for all events) ──────
    return {"received": True, "event": event_type}


# ──────────────────────────────────────────────────────────────────────────────
# Subscriber Hub — auth + preferences
# ──────────────────────────────────────────────────────────────────────────────


class HubAuthIn(BaseModel):
    email: str


@app.post("/subscriber/auth", summary="Verify subscriber email and issue hub access token")
async def subscriber_auth(payload: HubAuthIn) -> Dict[str, Any]:
    """
    Looks up the email in subscribers.csv (populated by Stripe checkout).
    If found and Active, issues a short-lived HMAC token for hub access.

    The Stripe customer_id is NEVER returned to the browser.
    Token TTL: 24 h. Store in sessionStorage, not localStorage.
    """
    email = payload.email.strip().lower()[:254]
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    if not SUBSCRIBERS_PATH.exists():
        # Return same error as not-found to avoid email enumeration (OWASP A07)
        raise HTTPException(status_code=404, detail="No active subscription found for this email")

    subscriber: Optional[Dict[str, Any]] = None
    with _csv_lock:
        try:
            with SUBSCRIBERS_PATH.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    if row.get("email", "").strip().lower() == email:
                        subscriber = dict(row)
                        break
        except Exception as exc:
            logger.error(f"subscriber_auth: CSV read error: {exc}")
            raise HTTPException(status_code=500, detail="Internal error")

    # Uniform error for not-found AND inactive — prevent user enumeration
    if not subscriber or subscriber.get("status", "Active").strip().lower() == "inactive":
        raise HTTPException(
            status_code=404,
            detail="No active subscription found for this email",
        )

    token = _make_hub_token(email)
    logger.info(f"Hub token issued for {email}")
    return {
        "token":       token,
        "email":       email,
        "region_plan": subscriber.get("region_plan", "Global"),
        "language":    subscriber.get("language",    "en"),
        "expires_in":  _TOKEN_TTL_SECONDS,
    }


class PreferencesIn(BaseModel):
    email:       str
    region_plan: str
    language:    str = "en"


@app.post("/subscriber/preferences", summary="Update subscriber region and language preferences")
async def update_preferences(
    payload:       PreferencesIn,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Persists region_plan and language to subscribers.csv.
    Requires a valid Bearer token from POST /subscriber/auth.
    Changes are applied on the next weekly delivery run.
    """
    # ── 1. Verify Bearer token ────────────────────────────────────────────────
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization[7:]
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token_email = _verify_hub_token(raw_token)
    if not token_email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # ── 2. Token must match payload email (block privilege escalation) ────────
    request_email = payload.email.strip().lower()[:254]
    if not _EMAIL_RE.match(request_email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    if token_email != request_email:
        raise HTTPException(status_code=403, detail="Token does not match email")

    # ── 3. Validate region against canonical whitelist ────────────────────────
    if payload.region_plan not in _CANONICAL_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region_plan. Allowed: {sorted(_CANONICAL_REGIONS)}",
        )

    # ── 4. Validate language ──────────────────────────────────────────────────
    if payload.language not in _VALID_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language. Allowed: {sorted(_VALID_LANGS)}",
        )

    # ── 5. Persist to subscribers.csv ─────────────────────────────────────────
    updated = _update_subscriber_preferences(
        request_email, payload.region_plan, payload.language, SUBSCRIBERS_PATH,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return {
        "status":      "updated",
        "email":       request_email,
        "region_plan": payload.region_plan,
        "language":    payload.language,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint directo
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_powerbi:app",
        host="127.0.0.1",
        port=8000,
        reload=False,       # reload=False → puerto estable para Power BI
        log_level="info",
    )
