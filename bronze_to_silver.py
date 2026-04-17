"""
bronze_to_silver.py — GameRadar AI Silver Layer
================================================

Lee todos los JSON de /bronze (descargados por GitHub Actions),
traduce campos de texto desde idiomas asiáticos al inglés usando
deep-translator, calcula el GameRadar Score y guarda un archivo
consolidado en /silver/silver_data.json.

GameRadar Score = (KDA * 0.3) + (WinRate * 0.4) + (ConsistencyIndex * 0.3)

Idiomas de origen soportados:
    zh-CN  — Chino Simplificado (LPL / China)
    zh-TW  — Chino Tradicional / Cantonés (Taiwan / HK)
    ja     — Japonés
    hi     — Hindi
    th     — Thai
    ko     — Coreano
    vi     — Vietnamita

Uso:
    python bronze_to_silver.py
    python bronze_to_silver.py --bronze-dir ./bronze --output silver/silver_data.json
    python bronze_to_silver.py --no-translate        # skip traducción (más rápido)
    python bronze_to_silver.py --since 2026-04-01    # solo archivos desde esa fecha
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# ──────────────────────────────────────────────────────────────────────────────
# Importar deep-translator con fallback informativo
# ──────────────────────────────────────────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator
    from deep_translator.exceptions import (
        NotValidPayload,
        RequestError,
        TooManyRequests,
    )
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning(
        "deep-translator no instalado. "
        "Instala con: pip install deep-translator==1.11.4\n"
        "Continúa sin traducción."
    )

# ──────────────────────────────────────────────────────────────────────────────
# Importar langdetect con fallback
# ──────────────────────────────────────────────────────────────────────────────
try:
    from langdetect import detect as _langdetect
    from langdetect import LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────────────

BRONZE_DIR  = pathlib.Path("bronze")
SILVER_DIR  = pathlib.Path("silver")
TODAY       = date.today().isoformat()
RUN_TS      = datetime.now(timezone.utc).isoformat()

# Campos de texto que pueden contener idiomas no-ingleses
TRANSLATABLE_FIELDS = ["nickname", "real_name", "team", "role", "rank"]

# Idiomas asiáticos que deep-translator reconoce → traducir al inglés
ASIAN_LANG_CODES = {
    "zh-CN", "zh-TW", "zh",    # Chino Simplificado / Tradicional / Cantonés
    "ja",                        # Japonés
    "hi",                        # Hindi
    "th",                        # Thai
    "ko",                        # Coreano
    "vi",                        # Vietnamita
}

# Mapeo country_code → idioma probable del campo (para traducción directa
# sin langdetect, usada cuando el texto es demasiado corto para detección)
COUNTRY_TO_LANG: Dict[str, str] = {
    "CN": "zh-CN",
    "TW": "zh-TW",
    "HK": "zh-TW",
    "JP": "ja",
    "IN": "hi",
    "TH": "th",
    "KR": "ko",
    "VN": "vi",
}

# Pesos del GameRadar Score
W_KDA         = 0.30
W_WIN_RATE    = 0.40
W_CONSISTENCY = 0.30

# Retardo mínimo entre llamadas a Google Translate (ms) — evitar rate-limiting
TRANSLATE_DELAY_MS = 200

# ──────────────────────────────────────────────────────────────────────────────
# Caché de traducciones — evita llamadas repetidas para el mismo texto
# ──────────────────────────────────────────────────────────────────────────────
_translation_cache: Dict[Tuple[str, str], str] = {}


def _detect_language(text: str) -> Optional[str]:
    """Intenta detectar el idioma de un texto. Devuelve código o None."""
    if not LANGDETECT_AVAILABLE or not text or len(text) < 3:
        return None
    try:
        return _langdetect(text)
    except LangDetectException:
        return None


def _translate_text(text: str, source_lang: str) -> str:
    """
    Traduce `text` desde `source_lang` al inglés usando GoogleTranslator.
    Usa caché interno. Respeta TRANSLATE_DELAY_MS entre llamadas.
    Devuelve el texto original si la traducción falla.
    """
    if not TRANSLATOR_AVAILABLE or not text or not text.strip():
        return text

    cache_key = (text, source_lang)
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    try:
        time.sleep(TRANSLATE_DELAY_MS / 1000)
        translated = GoogleTranslator(source=source_lang, target="en").translate(text)
        result = translated if translated else text
        _translation_cache[cache_key] = result
        return result
    except TooManyRequests:
        logger.warning("⚠️  Google Translate rate limit — esperando 5s…")
        time.sleep(5)
        return text
    except (NotValidPayload, RequestError, Exception) as exc:
        logger.debug(f"  Traducción fallida ({source_lang}→en): '{text[:40]}' — {exc}")
        return text


def translate_record_fields(record: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Traduce los campos de texto de un registro bronze al inglés.

    Estrategia:
      1. Para cada campo traducible, intenta detectar el idioma.
      2. Si el idioma detectado está en ASIAN_LANG_CODES → traduce.
      3. Si langdetect no puede detectar (texto corto) y el country_code
         sugiere un idioma asiático → traduce con ese idioma como fuente.
      4. Si el texto ya parece inglés / ASCII → no toca.

    Devuelve (record_con_campos_traducidos, n_traducciones_realizadas).
    """
    translated = dict(record)
    country = record.get("country", "XX")
    fallback_lang = COUNTRY_TO_LANG.get(country)
    n = 0

    for field in TRANSLATABLE_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            continue

        # Texto puramente ASCII → ya en inglés o ID, no traducir
        if value.isascii():
            continue

        # Detectar idioma
        detected = _detect_language(value)

        if detected in ASIAN_LANG_CODES:
            source = detected
        elif fallback_lang and not value.isascii():
            # Texto no-ASCII + país asiático conocido → usar fallback
            source = fallback_lang
        else:
            continue  # No hay evidencia de idioma asiático

        original = value
        translated_value = _translate_text(value, source)
        if translated_value != original:
            translated[field] = translated_value
            translated[f"{field}_original"] = original
            translated[f"{field}_source_lang"] = source
            n += 1

    return translated, n


# ──────────────────────────────────────────────────────────────────────────────
# Normalización de métricas
# ──────────────────────────────────────────────────────────────────────────────

def _safe_float(value: Any, default: float = 0.0,
                min_val: float = 0.0, max_val: float = float("inf")) -> float:
    """Convierte a float con fallback y rango de validez."""
    if value is None:
        return default
    try:
        f = float(value)
        if not math.isfinite(f):
            return default
        return max(min_val, min(f, max_val))
    except (TypeError, ValueError):
        return default


def _normalize_kda(kda: float) -> float:
    """
    Normaliza KDA a [0, 10] para que sea comparable con WinRate (0-100)
    escalado a 0-10 y ConsistencyIndex (0-100) escalado a 0-10.

    KDA típico pro: 2-8. Cap en 15 para no saturar outliers.
    Fórmula: min(kda, 15) / 15 * 10
    """
    return min(kda, 15.0) / 15.0 * 10.0


def _normalize_win_rate(win_rate: float) -> float:
    """Normaliza WinRate [0,100] → [0,10]."""
    return _safe_float(win_rate, 0.0, 0.0, 100.0) / 10.0


def _normalize_consistency(consistency: float) -> float:
    """Normaliza ConsistencyIndex [0,100] → [0,10]."""
    return _safe_float(consistency, 0.0, 0.0, 100.0) / 10.0


def _build_consistency_index(stats: Dict[str, Any], record: Dict[str, Any]) -> float:
    """
    Construye el Consistency Index cuando no viene explícito en los datos.

    Lógica heurística (orden de prioridad):
      1. consistency_score (TEC India, Soha Game)
      2. games_analyzed / 100 * 10  (proxy de actividad)
      3. tournament_participations normalizado
      4. 5.0 (valor neutro por defecto)
    """
    # Fuente directa
    cs = stats.get("consistency_score")
    if cs is not None:
        return _safe_float(cs, 5.0, 0.0, 100.0)

    # Proxy: actividad medida por partidas analizadas
    games = _safe_float(stats.get("games_analyzed"), 0.0, 0.0, 5000.0)
    if games > 0:
        # Escala: 100 partidas = 5.0, 500+ = 10.0
        return min(games / 50.0, 100.0)

    # Proxy: participación en torneos
    tp = _safe_float(stats.get("tournament_participations"), 0.0, 0.0, 500.0)
    if tp > 0:
        return min(tp * 2.0, 100.0)

    # Valor neutro
    return 50.0


def compute_gameradar_score(
    kda: float,
    win_rate: float,
    consistency_index: float,
) -> float:
    """
    GameRadar Score (escala 0–10):
        score = (KDA_norm * 0.3) + (WinRate_norm * 0.4) + (Consistency_norm * 0.3)

    Todas las métricas están normalizadas a [0,10] antes de aplicar pesos.
    """
    kda_n   = _normalize_kda(kda)
    wr_n    = _normalize_win_rate(win_rate)
    cons_n  = _normalize_consistency(consistency_index)

    score = (kda_n * W_KDA) + (wr_n * W_WIN_RATE) + (cons_n * W_CONSISTENCY)
    return round(score, 4)


def compute_score_breakdown(
    kda: float,
    win_rate: float,
    consistency_index: float,
) -> Dict[str, Any]:
    """Devuelve score + desglose de componentes para trazabilidad."""
    kda_n   = _normalize_kda(kda)
    wr_n    = _normalize_win_rate(win_rate)
    cons_n  = _normalize_consistency(consistency_index)

    return {
        "gameradar_score":      round((kda_n * W_KDA) + (wr_n * W_WIN_RATE) + (cons_n * W_CONSISTENCY), 4),
        "score_components": {
            "kda_raw":              round(kda, 4),
            "kda_normalized":       round(kda_n, 4),
            "kda_weighted":         round(kda_n * W_KDA, 4),
            "win_rate_raw":         round(win_rate, 4),
            "win_rate_normalized":  round(wr_n, 4),
            "win_rate_weighted":    round(wr_n * W_WIN_RATE, 4),
            "consistency_raw":      round(consistency_index, 4),
            "consistency_normalized": round(cons_n, 4),
            "consistency_weighted": round(cons_n * W_CONSISTENCY, 4),
        },
        "score_formula": f"({round(kda_n,3)} × {W_KDA}) + ({round(wr_n,3)} × {W_WIN_RATE}) + ({round(cons_n,3)} × {W_CONSISTENCY})",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Lectura de /bronze
# ──────────────────────────────────────────────────────────────────────────────

def _collect_bronze_files(
    bronze_dir: pathlib.Path,
    since: Optional[str] = None,
) -> List[Tuple[str, pathlib.Path]]:
    """
    Devuelve lista de (source_name, path) para todos los JSON en /bronze.
    Si `since` está dado (YYYY-MM-DD), solo incluye archivos desde esa fecha.
    """
    if not bronze_dir.exists():
        logger.error(
            f"❌  El directorio bronze no existe: {bronze_dir.resolve()}\n"
            "   Ejecuta primero el pipeline de ingesta (GitHub Actions o local):\n"
            "   python ingest_bronze_targets.py"
        )
        return []

    pairs: List[Tuple[str, pathlib.Path]] = []
    for src_dir in sorted(bronze_dir.iterdir()):
        if not src_dir.is_dir() or src_dir.name == "logs":
            continue
        for json_file in sorted(src_dir.glob("*.json")):
            if since:
                file_date = json_file.stem
                if file_date < since:
                    continue
            pairs.append((src_dir.name, json_file))
    return pairs


def load_bronze_records(
    bronze_dir: pathlib.Path,
    since: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Lee todos los archivos JSON de /bronze y devuelve lista plana de registros,
    añadiendo metadatos de origen: _source, _bronze_file, _bronze_date.
    """
    all_records: List[Dict[str, Any]] = []
    files = _collect_bronze_files(bronze_dir, since)

    if not files:
        logger.warning(f"⚠️  No se encontraron archivos JSON en {bronze_dir}")
        return []

    for source_name, json_file in files:
        try:
            # utf-8-sig strips BOM if present, otherwise reads normally
            data = json.loads(json_file.read_text(encoding="utf-8-sig"))
            if not isinstance(data, list):
                logger.warning(f"  ⚠️  {json_file}: no es lista — saltando")
                continue
            for rec in data:
                rec["_source"]      = source_name
                rec["_bronze_file"] = str(json_file)
                rec["_bronze_date"] = json_file.stem
            all_records.extend(data)
            logger.debug(f"  📂 {source_name}/{json_file.name}: {len(data)} registros")
        except json.JSONDecodeError as exc:
            logger.warning(f"  ⚠️  JSON inválido en {json_file}: {exc}")
        except Exception as exc:
            logger.warning(f"  ⚠️  Error leyendo {json_file}: {exc}")

    return all_records


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline bronze → silver
# ──────────────────────────────────────────────────────────────────────────────

def process_record(
    record: Dict[str, Any],
    translate: bool = True,
) -> Dict[str, Any]:
    """
    Transforma un registro bronze en un registro silver:
      1. Traduce campos de texto no-ingleses al inglés
      2. Extrae y normaliza métricas (KDA, WinRate, ConsistencyIndex)
      3. Calcula GameRadar Score
      4. Adjunta metadatos de procesamiento
    """
    # ── Traducción ──────────────────────────────────────────────────────────
    n_translations = 0
    if translate and TRANSLATOR_AVAILABLE:
        record, n_translations = translate_record_fields(record)

    # ── Extracción de métricas ───────────────────────────────────────────────
    stats_raw = record.get("stats") or {}

    kda        = _safe_float(stats_raw.get("kda"),      0.0, 0.0, 50.0)
    win_rate   = _safe_float(stats_raw.get("win_rate"), 0.0, 0.0, 100.0)
    consistency = _build_consistency_index(stats_raw, record)

    # ── Calcular score ───────────────────────────────────────────────────────
    breakdown = compute_score_breakdown(kda, win_rate, consistency)

    # ── Enriquecer stats con consistency_index normalizado ───────────────────
    stats_silver = dict(stats_raw)
    stats_silver["consistency_index"] = round(consistency, 4)

    # ── Construir registro silver ────────────────────────────────────────────
    silver: Dict[str, Any] = {
        # Identidad
        "nickname":     record.get("nickname"),
        "real_name":    record.get("real_name"),
        "team":         record.get("team"),
        "role":         record.get("role"),
        "rank":         record.get("rank"),
        "country":      record.get("country", "XX"),
        "server":       record.get("server"),
        "game":         record.get("game", "LOL"),
        "profile_url":  record.get("profile_url") or record.get("raw_url"),

        # Score GameRadar
        **breakdown,

        # Métricas enriquecidas
        "stats": stats_silver,

        # Metadatos silver
        "_source":          record.get("_source"),
        "_bronze_file":     record.get("_bronze_file"),
        "_bronze_date":     record.get("_bronze_date"),
        "_silver_ts":       RUN_TS,
        "_partial":         record.get("_partial", False),
        "_translations_applied": n_translations,
    }

    # Limpiar Nones superfluos
    return {k: v for k, v in silver.items() if v is not None or k in (
        "nickname", "gameradar_score", "_source", "_partial"
    )}


def deduplicate(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplica por (nickname, source). Cuando hay duplicados (varios días),
    conserva el registro con mayor gameradar_score.
    """
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for rec in records:
        key = (
            (rec.get("nickname") or "").lower().strip(),
            rec.get("_source", ""),
        )
        if key not in index:
            index[key] = rec
        else:
            existing_score = index[key].get("gameradar_score", 0.0) or 0.0
            new_score      = rec.get("gameradar_score", 0.0) or 0.0
            if new_score > existing_score:
                index[key] = rec
    return list(index.values())


def build_summary(silver_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Genera métricas de ejecución para el archivo de summary."""
    by_source: Dict[str, List[float]] = {}
    for rec in silver_records:
        src = rec.get("_source", "unknown")
        score = rec.get("gameradar_score")
        if score is not None:
            by_source.setdefault(src, []).append(score)

    source_stats = {}
    for src, scores in sorted(by_source.items()):
        scores_sorted = sorted(scores, reverse=True)
        source_stats[src] = {
            "count":    len(scores),
            "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
            "max_score": round(max(scores), 4),
            "min_score": round(min(scores), 4),
            "top_3_scores": [round(s, 4) for s in scores_sorted[:3]],
        }

    all_scores = [r["gameradar_score"] for r in silver_records if r.get("gameradar_score") is not None]

    return {
        "run_ts":           RUN_TS,
        "total_records":    len(silver_records),
        "sources_covered":  len(by_source),
        "translations_applied": sum(r.get("_translations_applied", 0) for r in silver_records),
        "avg_gameradar_score": round(sum(all_scores) / len(all_scores), 4) if all_scores else 0,
        "score_formula":    f"(KDA_norm×{W_KDA}) + (WinRate_norm×{W_WIN_RATE}) + (Consistency_norm×{W_CONSISTENCY})",
        "normalization_note": "Todas las métricas normalizadas a [0,10] antes de ponderar. Score final en [0,10].",
        "by_source":        source_stats,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main(
    bronze_dir: pathlib.Path = BRONZE_DIR,
    output_path: pathlib.Path = SILVER_DIR / "silver_data.json",
    translate: bool = True,
    since: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    logger.info("=" * 70)
    logger.info("🥈  GameRadar AI — Bronze → Silver Pipeline")
    logger.info(f"   Bronze dir : {bronze_dir.resolve()}")
    logger.info(f"   Output     : {output_path.resolve()}")
    logger.info(f"   Traducción : {'✅  sí' if translate and TRANSLATOR_AVAILABLE else '⛔  no'}")
    logger.info(f"   Desde      : {since or 'todos los archivos'}")
    logger.info(f"   Dry-run    : {dry_run}")
    logger.info("=" * 70)

    # ── 1. Leer bronze ─────────────────────────────────────────────────────
    logger.info("\n📂  Leyendo archivos bronze…")
    bronze_records = load_bronze_records(bronze_dir, since=since)
    if not bronze_records:
        logger.error("❌  Sin registros bronze. ¿Existe /bronze con archivos JSON?")
        sys.exit(0 if dry_run else 1)
    logger.info(f"   {len(bronze_records)} registros cargados desde bronze.")

    # ── 2. Procesar: traducir + score ───────────────────────────────────────
    logger.info("\n⚙️   Procesando registros (traducción + GameRadar Score)…")
    silver_records: List[Dict[str, Any]] = []
    total_translations = 0

    for i, rec in enumerate(bronze_records, 1):
        silver_rec = process_record(rec, translate=translate)
        silver_records.append(silver_rec)
        total_translations += silver_rec.get("_translations_applied", 0)

        if i % 10 == 0 or i == len(bronze_records):
            logger.info(f"   {i}/{len(bronze_records)} procesados…")

    # ── 3. Deduplicar ───────────────────────────────────────────────────────
    pre_dedup = len(silver_records)
    silver_records = deduplicate(silver_records)
    logger.info(f"\n🔗  Deduplicación: {pre_dedup} → {len(silver_records)} registros únicos.")

    # ── 4. Ordenar por score descendente ────────────────────────────────────
    silver_records.sort(
        key=lambda r: r.get("gameradar_score") or 0.0,
        reverse=True,
    )

    # ── 5. Construir payload final ──────────────────────────────────────────
    summary = build_summary(silver_records)
    payload = {
        "_meta": summary,
        "players": silver_records,
    }

    # ── 6. Guardar ──────────────────────────────────────────────────────────
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.success(f"\n💾  Guardado: {output_path}  ({len(silver_records)} jugadores)")
    else:
        logger.info("\n[DRY-RUN] No se escribió silver_data.json")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000] + "\n…[truncado]")

    # ── 7. Resumen consola ──────────────────────────────────────────────────
    logger.info("\n" + "=" * 70)
    logger.info("📊  RESUMEN SILVER")
    logger.info(f"   Jugadores únicos : {summary['total_records']}")
    logger.info(f"   Fuentes cubiertas: {summary['sources_covered']}")
    logger.info(f"   Traducciones     : {summary['translations_applied']}")
    logger.info(f"   Score promedio   : {summary['avg_gameradar_score']:.4f} / 10")

    if silver_records:
        top = silver_records[0]
        logger.info(
            f"\n🏆  Top jugador: {top.get('nickname')} "
            f"({top.get('_source')}) "
            f"→ score {top.get('gameradar_score')}"
        )

    logger.info("\n   Por fuente:")
    for src, stats in summary["by_source"].items():
        logger.info(
            f"     {src:<20}: {stats['count']:>3} jugadores, "
            f"avg={stats['avg_score']:.3f}, max={stats['max_score']:.3f}"
        )
    logger.info("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GameRadar AI — Bronze to Silver pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python bronze_to_silver.py
  python bronze_to_silver.py --no-translate
  python bronze_to_silver.py --since 2026-04-01
  python bronze_to_silver.py --bronze-dir ./bronze --output silver/silver_data.json
  python bronze_to_silver.py --dry-run
        """,
    )
    parser.add_argument(
        "--bronze-dir",
        type=pathlib.Path,
        default=BRONZE_DIR,
        help=f"Carpeta raíz de bronze (default: {BRONZE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=SILVER_DIR / "silver_data.json",
        help="Ruta del archivo silver de salida",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Omitir traducción (útil para debugging o sin conexión)",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Solo procesar archivos bronze desde esta fecha",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar sin escribir archivos",
    )

    args = parser.parse_args()

    main(
        bronze_dir  = args.bronze_dir,
        output_path = args.output,
        translate   = not args.no_translate,
        since       = args.since,
        dry_run     = args.dry_run,
    )
