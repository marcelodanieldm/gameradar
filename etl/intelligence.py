"""
intelligence.py — GameRadar AI NLP & Scoring Intelligence Module
=================================================================

Two responsibilities:

1. E-SPORTS TERM TRANSLATION
   Maps roles, items and abilities from 7 Asian languages to canonical
   English using a two-tier approach:
     - Tier 1: Technical Mapping dictionary  — guaranteed exact matches
       (ADC, Jungler, Flash, etc.)  regardless of source language.
     - Tier 2: deep-translator (Google Translate) — falls back for any
       term not covered by the technical dictionary.

   Supported languages
   ───────────────────
   zh-CN  Mandarin Chinese    (LPL / iG / TES)
   zh-TW  Cantonese / Trad.   (HK / Taiwan)
   ko     Korean              (LCK / T1 / DK)
   ja     Japanese            (LJL / ZETA / DetonatioN)
   hi     Hindi               (India / Tec)
   th     Thai                (Thailand)
   vi     Vietnamese          (VCS)

2. ROOKIE PLAN SCORING
   Score = (KDA × 0.35) + (WinRate × 0.45) + (Match_Frequency × 0.20)

   All metrics are normalised to [0, 10] before weighting.
   A per-region difficulty multiplier is applied before final ranking:
     Korea  × 1.20  (LCK — world's most competitive server)
     India  × 0.90  (developing competitive scene)

Public API
──────────
    translate_esports_term(text, source_lang)  → str
    translate_player_record(record)            → dict
    score_player(kda, win_rate, games, country) → ScoredPlayer (namedtuple)
    score_dataframe(df)                        → pd.DataFrame  (sorted ranking)
    rank_players(records)                      → pd.DataFrame
"""

from __future__ import annotations

import math
import time
from typing import NamedTuple

import pandas as pd
from loguru import logger

# ── Optional deep-translator import ──────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator
    from deep_translator.exceptions import NotValidPayload, RequestError, TooManyRequests
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False
    logger.warning(
        "deep-translator not installed — Google Translate fallback disabled. "
        "Run: pip install deep-translator==1.11.4"
    )

# ── Optional langdetect import ────────────────────────────────────────────────
try:
    from langdetect import detect as _langdetect, LangDetectException
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONSTANTS & TECHNICAL MAPPING DICTIONARY
# ══════════════════════════════════════════════════════════════════════════════

# Minimum delay between Google Translate calls (seconds)
_TRANSLATE_DELAY = 0.20

# In-process cache to avoid repeated API calls for the same (text, lang) pair
_translation_cache: dict[tuple[str, str], str] = {}

# Languages that use non-ASCII scripts → primary candidates for translation
_ASIAN_LANG_CODES: set[str] = {"zh-CN", "zh-TW", "zh", "ko", "ja", "hi", "th", "vi"}

# Country → most likely language (used when text is too short for langdetect)
COUNTRY_TO_LANG: dict[str, str] = {
    "CN": "zh-CN",
    "TW": "zh-TW",
    "HK": "zh-TW",
    "KR": "ko",
    "JP": "ja",
    "IN": "hi",
    "TH": "th",
    "VN": "vi",
}

# ─────────────────────────────────────────────────────────────────────────────
# TECHNICAL MAPPING — Tier 1 (exact, guaranteed)
#
# Structure: {source_lang: {native_term: canonical_english}}
#
# Covers:
#   • Roles        (ADC, Jungler, Support, Mid, Top, Fill …)
#   • Core items   (Trinity Force, Rabadon's, Infinity Edge …)
#   • Key spells   (Flash, Ignite, Teleport …)
#   • Meta terms   (Carry, Poke, Engage, Dive, Peel …)
# ─────────────────────────────────────────────────────────────────────────────

TECHNICAL_MAPPING: dict[str, dict[str, str]] = {

    # ── Mandarin Chinese (Simplified) ─────────────────────────────────────────
    "zh-CN": {
        # Roles
        "射手":   "ADC",
        "ADC":    "ADC",
        "打野":   "Jungler",
        "中单":   "Mid",
        "上单":   "Top",
        "辅助":   "Support",
        "补位":   "Fill",
        # Meta terms
        "核心":   "Carry",
        "骚扰型": "Poke",
        "坦克":   "Tank",
        "法师":   "Mage",
        "刺客":   "Assassin",
        "战士":   "Fighter",
        "前期强势":"Early Game",
        "后期强势":"Late Game",
        "开团":   "Engage",
        "保护":   "Peel",
        "推线":   "Split Push",
        "控场":   "Crowd Control",
        "团战":   "Teamfight",
        # Items (common abbreviations)
        "三相之力": "Trinity Force",
        "无尽之刃": "Infinity Edge",
        "拉博顿帽": "Rabadon's Deathcap",
        "电刀":    "Statikk Shiv",
        "冰杖":    "Frozen Mallet",
        # Summoner spells
        "闪现":   "Flash",
        "点燃":   "Ignite",
        "传送":   "Teleport",
        "清除":   "Cleanse",
        "净化":   "Purify",
        "屏障":   "Barrier",
        "治疗":   "Heal",
        "虚弱":   "Exhaust",
        "幽灵疾步":"Ghost",
        # ── Gameplay mechanics (20 new — DoD #2) ──────────────────────────────
        "打野袭击": "Gank",
        "抓人":    "Gank",
        "补兵":    "CS",
        "目标控制": "Objective Control",
        "大龙":    "Baron",
        "大龙坑":  "Baron",
        "小龙":    "Dragon",
        "游走":    "Roaming",
        "眼位":    "Ward",
        "视野控制": "Vision Control",
        "反野":    "Counter Jungle",
        "侵入":    "Invade",
        "滚雪球":  "Snowball",
        "后期发育": "Scaling",
        "超级核心": "Hypercarry",
        "强行进攻": "Dive",
        "风筝":    "Kite",
        "绕后":    "Flank",
        "辅助功能": "Utility",
        "硬控":    "Hard CC",
        "爆发":    "Burst",
        "对线期":  "Laning Phase",
    },

    # ── Cantonese / Traditional Chinese ──────────────────────────────────────
    "zh-TW": {
        # Roles
        "射手":   "ADC",
        "打野":   "Jungler",
        "中路":   "Mid",
        "上路":   "Top",
        "輔助":   "Support",
        "補位":   "Fill",
        # Meta
        "核心":   "Carry",
        "坦克":   "Tank",
        "法師":   "Mage",
        "刺客":   "Assassin",
        "戰士":   "Fighter",
        "騷擾型": "Poke",
        "前期強勢":"Early Game",
        "後期強勢":"Late Game",
        "開團":   "Engage",
        "保護":   "Peel",
        "推線":   "Split Push",
        "控場":   "Crowd Control",
        "團戰":   "Teamfight",
        # Items
        "三相之力": "Trinity Force",
        "無盡之刃": "Infinity Edge",
        "拉博頓帽": "Rabadon's Deathcap",
        # Spells
        "閃現":   "Flash",
        "點燃":   "Ignite",
        "傳送":   "Teleport",
        "淨化":   "Cleanse",
        "屏障":   "Barrier",
        "治療":   "Heal",
        "疲憊":   "Exhaust",
        "幽靈疾步":"Ghost",
        # ── Gameplay mechanics (DoD #2) ───────────────────────────────────────
        "打野埋伏": "Gank",
        "補兵":    "CS",
        "目標控制": "Objective Control",
        "大龍":    "Baron",
        "小龍":    "Dragon",
        "游走":    "Roaming",
        "眼位":    "Ward",
        "視野控制": "Vision Control",
        "反野":    "Counter Jungle",
        "侵入":    "Invade",
        "滾雪球":  "Snowball",
        "後期發育": "Scaling",
        "超級核心": "Hypercarry",
        "強攻":    "Dive",
        "風箏":    "Kite",
        "繞後":    "Flank",
        "輔助功能": "Utility",
        "硬控":    "Hard CC",
        "爆發":    "Burst",
        "對線期":  "Laning Phase",
    },

    # ── Korean ────────────────────────────────────────────────────────────────
    "ko": {
        # Roles
        "원딜":   "ADC",
        "ADC":    "ADC",
        "정글":   "Jungler",
        "미드":   "Mid",
        "탑":     "Top",
        "서포터": "Support",
        "필":     "Fill",
        "원거리딜러": "ADC",
        # Meta
        "캐리":   "Carry",
        "탱커":   "Tank",
        "마법사": "Mage",
        "암살자": "Assassin",
        "전사":   "Fighter",
        "포크":   "Poke",
        "이니시에이터": "Engage",
        "필":     "Peel",
        "스플릿 푸시": "Split Push",
        "군중제어": "Crowd Control",
        "팀파이트": "Teamfight",
        "초반강세": "Early Game",
        "후반강세": "Late Game",
        # Items
        "삼위일체": "Trinity Force",
        "무한의 대검": "Infinity Edge",
        "라바돈의 죽음 모자": "Rabadon's Deathcap",
        # Spells
        "점멸":   "Flash",
        "점화":   "Ignite",
        "순간이동": "Teleport",
        "정화":   "Cleanse",
        "방어막": "Barrier",
        "회복":   "Heal",
        "탈진":   "Exhaust",
        "유체화": "Ghost",
        # ── Gameplay mechanics (DoD #2) ───────────────────────────────────────
        "갱크":     "Gank",
        "CS":      "CS",
        "오브젝트 관리": "Objective Control",
        "바론":     "Baron",
        "드래곤":   "Dragon",
        "로밍":     "Roaming",
        "와드":     "Ward",
        "시야 장악": "Vision Control",
        "카정":     "Counter Jungle",
        "인베":     "Invade",
        "스노우볼":  "Snowball",
        "스케일링":  "Scaling",
        "하이퍼캐리": "Hypercarry",
        "다이브":   "Dive",
        "카이팅":   "Kite",
        "플랭크":   "Flank",
        "유틸리티":  "Utility",
        "하드 CC":  "Hard CC",
        "버스트":   "Burst",
        "라인전":   "Laning Phase",
    },

    # ── Japanese ──────────────────────────────────────────────────────────────
    "ja": {
        # Roles
        "ADC":    "ADC",
        "ジャングル": "Jungler",
        "ミッド":  "Mid",
        "トップ":  "Top",
        "サポート": "Support",
        "フィル":  "Fill",
        "マークスマン": "ADC",
        # Meta
        "キャリー": "Carry",
        "タンク":  "Tank",
        "メイジ":  "Mage",
        "アサシン": "Assassin",
        "ファイター": "Fighter",
        "ポーク":  "Poke",
        "エンゲージ": "Engage",
        "ピール":  "Peel",
        "スプリットプッシュ": "Split Push",
        "CC":     "Crowd Control",
        "チームファイト": "Teamfight",
        # Items
        "トリニティフォース": "Trinity Force",
        "インフィニティエッジ": "Infinity Edge",
        "ラバドンのデスキャップ": "Rabadon's Deathcap",
        # Spells
        "フラッシュ": "Flash",
        "イグナイト": "Ignite",
        "テレポート": "Teleport",
        "クレンズ": "Cleanse",
        "バリア":  "Barrier",
        "ヒール":  "Heal",
        "イグゾースト": "Exhaust",
        "ゴースト": "Ghost",
        # ── Gameplay mechanics (DoD #2) ───────────────────────────────────────
        "ガンク":             "Gank",
        "CS":                "CS",
        "オブジェクト管理":   "Objective Control",
        "バロン":             "Baron",
        "ドラゴン":           "Dragon",
        "ローミング":         "Roaming",
        "ワード":             "Ward",
        "視界管理":           "Vision Control",
        "カウンタージャングル": "Counter Jungle",
        "インベード":         "Invade",
        "スノーボール":       "Snowball",
        "スケーリング":       "Scaling",
        "ハイパーキャリー":   "Hypercarry",
        "ダイブ":             "Dive",
        "カイティング":       "Kite",
        "フランク":           "Flank",
        "ユーティリティ":     "Utility",
        "ハードCC":           "Hard CC",
        "バースト":           "Burst",
        "レーン戦":           "Laning Phase",
    },

    # ── Hindi ─────────────────────────────────────────────────────────────────
    "hi": {
        # Roles  (Devanagari transliterations used in Indian esports community)
        "एडीसी":    "ADC",
        "जंगलर":   "Jungler",
        "मिड":     "Mid",
        "टॉप":     "Top",
        "सपोर्ट":  "Support",
        "फिल":     "Fill",
        # Meta
        "कैरी":    "Carry",
        "टैंक":    "Tank",
        "मेज":     "Mage",
        "असैसिन":  "Assassin",
        "फाइटर":   "Fighter",
        "पोक":     "Poke",
        "एंगेज":   "Engage",
        "पील":     "Peel",
        "स्प्लिट पुश": "Split Push",
        "क्राउड कंट्रोल": "Crowd Control",
        "टीम फाइट": "Teamfight",
        # Spells
        "फ्लैश":   "Flash",
        "इग्नाइट": "Ignite",
        "टेलीपोर्ट": "Teleport",
        "हील":     "Heal",
        "बैरियर":  "Barrier",
        "एग्जॉस्ट": "Exhaust",
        "क्लेंज":  "Cleanse",
        "घोस्ट":   "Ghost",
        # ── Gameplay mechanics (DoD #2) ───────────────────────────────────────
        "गैंक":           "Gank",
        "सीएस":           "CS",
        "उद्देश्य नियंत्रण": "Objective Control",
        "बैरन":           "Baron",
        "ड्रैगन":         "Dragon",
        "रोमिंग":         "Roaming",
        "वार्ड":          "Ward",
        "दृष्टि नियंत्रण": "Vision Control",
        "काउंटर जंगल":    "Counter Jungle",
        "इनवेड":          "Invade",
        "स्नोबॉल":        "Snowball",
        "स्केलिंग":       "Scaling",
        "हाइपरकैरी":      "Hypercarry",
        "डाइव":           "Dive",
        "काइटिंग":        "Kite",
        "फ्लैंक":         "Flank",
        "यूटिलिटी":       "Utility",
        "हार्ड सीसी":     "Hard CC",
        "बर्स्ट":         "Burst",
        "लेन फेज":        "Laning Phase",
    },

    # ── Thai ──────────────────────────────────────────────────────────────────
    "th": {
        # Roles
        "ADC":    "ADC",
        "จังเกิล": "Jungler",
        "มิด":    "Mid",
        "ท็อป":   "Top",
        "ซัพพอร์ต": "Support",
        "ฟิล":    "Fill",
        # Meta
        "แคร์รี": "Carry",
        "แทงค์":  "Tank",
        "เมจ":    "Mage",
        "นักฆ่า": "Assassin",
        "ไฟเตอร์": "Fighter",
        "โพค":    "Poke",
        "เอนเกจ": "Engage",
        "พีล":    "Peel",
        "สปลิตพุช": "Split Push",
        "ควบคุมฝูงชน": "Crowd Control",
        "ทีมไฟท์": "Teamfight",
        # Spells
        "แฟลช":  "Flash",
        "อิกไนต์": "Ignite",
        "เทเลพอร์ต": "Teleport",
        "ฮีล":   "Heal",
        "แบร์เรีย": "Barrier",
        "คลีนซ์": "Cleanse",
        "เอ็กซ์ฮอสต์": "Exhaust",
        "โกสต์": "Ghost",
        # ── Gameplay mechanics (DoD #2) ───────────────────────────────────────
        "แกงค์":             "Gank",
        "CS":                "CS",
        "ควบคุมออบเจ็กต์":   "Objective Control",
        "บารอน":             "Baron",
        "มังกร":             "Dragon",
        "โรมมิ่ง":           "Roaming",
        "วอร์ด":             "Ward",
        "ควบคุมวิสัยทัศน์": "Vision Control",
        "เคาน์เตอร์จังเกิล": "Counter Jungle",
        "อินเวด":            "Invade",
        "สโนว์บอล":          "Snowball",
        "สเกลลิ่ง":          "Scaling",
        "ไฮเปอร์แคร์รี":     "Hypercarry",
        "ดิ้ว":              "Dive",
        "ไคทิ้ง":            "Kite",
        "แฟลงค์":            "Flank",
        "ยูทิลิตี้":         "Utility",
        "ฮาร์ดซีซี":         "Hard CC",
        "เบิร์สต์":          "Burst",
        "เลนเฟส":            "Laning Phase",
    },

    # ── Vietnamese ────────────────────────────────────────────────────────────
    "vi": {
        # Roles
        "xạ thủ":  "ADC",
        "ADC":     "ADC",
        "đi rừng": "Jungler",
        "trung tâm": "Mid",
        "đường trên": "Top",
        "hỗ trợ":  "Support",
        "lấp đầy": "Fill",
        # Meta
        "mang":    "Carry",
        "xe tăng": "Tank",
        "pháp sư": "Mage",
        "sát thủ": "Assassin",
        "chiến sĩ": "Fighter",
        "chọc":    "Poke",
        "mở đầu":  "Engage",
        "bảo vệ":  "Peel",
        "chia đẩy": "Split Push",
        "kiểm soát đám đông": "Crowd Control",
        "đánh nhóm": "Teamfight",
        # Spells
        "nhấp nháy": "Flash",
        "thiêu đốt": "Ignite",
        "dịch chuyển": "Teleport",
        "hồi phục": "Heal",
        "rào cản":  "Barrier",
        "thanh tẩy": "Cleanse",
        "kiệt sức": "Exhaust",
        "bóng ma":  "Ghost",
        # ── Gameplay mechanics (DoD #2) ──────────────────────────────────────
        "gank":                    "Gank",
        "phục kích":               "Gank",
        "CS":                      "CS",
        "kiểm soát mục tiêu":      "Objective Control",
        "baron":                   "Baron",
        "rồng":                    "Dragon",
        "roaming":                 "Roaming",
        "đi gank":                 "Roaming",
        "mắt":                     "Ward",
        "kiểm soát tầm nhìn":      "Vision Control",
        "phản rừng":               "Counter Jungle",
        "xâm phạm":                "Invade",
        "snowball":                 "Snowball",
        "leo thang":               "Scaling",
        "siêu carry":              "Hypercarry",
        "dive":                    "Dive",
        "kite":                    "Kite",
        "bọc hậu":                 "Flank",
        "tiện ích":                "Utility",
        "CC cứng":                 "Hard CC",
        "bùng phát":               "Burst",
        "giai đoạn đường":         "Laning Phase",
    },
}

# Flat reverse lookup: canonical_english → set of all native forms  (for logging)
_ALL_NATIVE_TERMS: set[str] = {
    native
    for lang_map in TECHNICAL_MAPPING.values()
    for native in lang_map
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — TRANSLATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def translate_esports_term(text: str, source_lang: str) -> str:
    """
    Translate a single esports term from `source_lang` to canonical English.

    Resolution order
    ────────────────
    1. Exact match in TECHNICAL_MAPPING[source_lang]          → guaranteed
    2. Case-insensitive / stripped match in the same dict
    3. Google Translate (deep-translator) via GoogleTranslator
    4. Return `text` unchanged if all methods fail

    Parameters
    ----------
    text        : Native-language esports term (e.g. "打野", "정글", "ジャングル")
    source_lang : BCP-47 language code ("zh-CN", "ko", "ja", "hi", "th", "vi", "zh-TW")

    Returns
    -------
    Canonical English term (e.g. "Jungler") or the original text on failure.
    """
    if not text or not text.strip():
        return text

    text_stripped = text.strip()

    # ── Tier 1: exact technical match ────────────────────────────────────────
    lang_map = TECHNICAL_MAPPING.get(source_lang, {})
    if text_stripped in lang_map:
        result = lang_map[text_stripped]
        logger.debug(f"  DICT  [{source_lang}] '{text_stripped}' → '{result}'")
        return result

    # Case-insensitive fallback within the same language map
    lower = text_stripped.lower()
    for native, canonical in lang_map.items():
        if native.lower() == lower:
            logger.debug(f"  DICT~ [{source_lang}] '{text_stripped}' → '{canonical}'")
            return canonical

    # ── Tier 2: Google Translate ──────────────────────────────────────────────
    if not _TRANSLATOR_AVAILABLE:
        logger.debug(f"  MISS  [{source_lang}] '{text_stripped}' — no translator available")
        return text_stripped

    cache_key = (text_stripped, source_lang)
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    try:
        time.sleep(_TRANSLATE_DELAY)
        translated = GoogleTranslator(source=source_lang, target="en").translate(text_stripped)
        result = translated.strip() if translated else text_stripped
        _translation_cache[cache_key] = result
        logger.debug(f"  API   [{source_lang}] '{text_stripped}' → '{result}'")
        return result
    except TooManyRequests:
        logger.warning(f"  LIMIT Google Translate rate limit — waiting 5 s …")
        time.sleep(5)
        return text_stripped
    except (NotValidPayload, RequestError, Exception) as exc:
        logger.debug(f"  FAIL  [{source_lang}] '{text_stripped}' — {exc}")
        return text_stripped


def translate_player_record(record: dict) -> dict:
    """
    Translate all esports-relevant text fields of a bronze/silver player record
    to canonical English.

    Fields translated: role, rank, team (if non-ASCII)
    Preserves original values as `*_original` keys for auditability.

    Parameters
    ----------
    record : dict  — single player record from bronze or master_rookie.json

    Returns
    -------
    dict — copy of `record` with translated fields (originals preserved).
    """
    out = dict(record)
    country = record.get("country", "XX")
    lang = COUNTRY_TO_LANG.get(country)

    _TRANSLATABLE = ("role", "rank", "team")

    for field in _TRANSLATABLE:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            continue

        # Skip purely ASCII values — already English
        if value.isascii():
            continue

        # Detect language if not deterministic from country code
        effective_lang = lang
        if effective_lang is None and _LANGDETECT_AVAILABLE:
            try:
                detected = _langdetect(value)
                if detected in _ASIAN_LANG_CODES:
                    effective_lang = detected
            except LangDetectException:
                pass

        if effective_lang is None:
            logger.debug(f"  SKIP  field='{field}' value='{value}' — cannot determine language")
            continue

        canonical = translate_esports_term(value, effective_lang)
        if canonical != value:
            out[field] = canonical
            out[f"{field}_original"] = value
            out[f"{field}_lang"] = effective_lang

    return out


def translate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply translate_player_record row-by-row to a DataFrame of player records.
    Returns a new DataFrame with translated columns.
    """
    logger.info(f"Translating {len(df)} player records …")
    records = df.to_dict(orient="records")
    translated = [translate_player_record(r) for r in records]
    result = pd.DataFrame(translated)
    changed = sum(
        1 for orig, trans in zip(records, translated)
        if any(orig.get(f) != trans.get(f) for f in ("role", "rank", "team"))
    )
    logger.info(f"Translation complete — {changed}/{len(df)} records had fields translated")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SCORING: ROOKIE PLAN FORMULA + REGIONAL MULTIPLIERS
# ══════════════════════════════════════════════════════════════════════════════

# ── Rookie Plan weights ───────────────────────────────────────────────────────
W_KDA             = 0.35
W_WIN_RATE        = 0.45
W_MATCH_FREQUENCY = 0.20

# ── Normalisation caps ───────────────────────────────────────────────────────
KDA_CAP        = 15.0   # Pro players rarely exceed 15 sustained KDA
WIN_RATE_CAP   = 100.0
GAMES_CAP      = 150.0  # 150 ranked games ≈ full competitive season

# ── Regional difficulty multipliers ─────────────────────────────────────────
#
# Rationale:
#   Korea (LCK, Challengers KR) is consistently the most competitive server
#   globally → scores here are "harder earned" → amplify by 1.20 to reflect
#   true comparative quality in a global ranking.
#
#   India is a developing scene with shallower competition depth → discount
#   by 0.90 to avoid inflating rankings with regionally-uncontested stats.
#
REGIONAL_MULTIPLIERS: dict[str, float] = {
    "KR": 1.20,   # Korea  — hardest server
    "IN": 0.90,   # India  — emerging scene
    # All other countries default to 1.00 (neutral)
}

_DEFAULT_MULTIPLIER = 1.00


class ScoredPlayer(NamedTuple):
    """Result of score_player(). All numeric fields rounded for readability."""
    nickname:            str
    country:             str
    role:                str
    kda:                 float
    win_rate:            float
    games_analyzed:      int
    kda_norm:            float   # normalised [0, 10]
    win_rate_norm:       float   # normalised [0, 10]
    match_freq_norm:     float   # normalised [0, 10]
    raw_score:           float   # weighted sum before multiplier [0, 10]
    difficulty_mult:     float   # regional multiplier
    final_score:         float   # raw_score × difficulty_mult, capped at 10
    source:              str


# ── Internal helpers ──────────────────────────────────────────────────────────

def _safe(value: object, default: float = 0.0,
          lo: float = 0.0, hi: float = 1e9) -> float:
    """Clamp-safe float conversion with fallback default."""
    try:
        f = float(value)  # type: ignore[arg-type]
        return max(lo, min(f, hi)) if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _norm_kda(kda: float) -> float:
    """KDA → [0, 10]  (capped at KDA_CAP)."""
    return round(min(kda, KDA_CAP) / KDA_CAP * 10.0, 6)


def _norm_win_rate(win_rate: float) -> float:
    """WinRate % → [0, 10]."""
    return round(_safe(win_rate, 0, 0, WIN_RATE_CAP) / WIN_RATE_CAP * 10.0, 6)


def _norm_match_frequency(games: float) -> float:
    """
    Match Frequency → [0, 10].

    Interpretation: games_analyzed as a proxy for competitive activity.
    150+ games = maximum score (full season).
    """
    return round(min(_safe(games, 0, 0, GAMES_CAP), GAMES_CAP) / GAMES_CAP * 10.0, 6)


# ── Public scoring API ────────────────────────────────────────────────────────

def score_player(
    kda:           float,
    win_rate:      float,
    games:         float,
    country:       str = "XX",
    *,
    nickname:      str = "Unknown",
    role:          str = "Unknown",
    source:        str = "",
) -> ScoredPlayer:
    """
    Compute the Rookie Plan GameRadar Score for one player.

    Formula
    ───────
        Score = (KDA_norm × 0.35) + (WinRate_norm × 0.45) + (MatchFreq_norm × 0.20)

    The raw score is then multiplied by the regional difficulty factor:
        final_score = raw_score × REGIONAL_MULTIPLIERS.get(country, 1.00)

    All norms in [0, 10].  final_score is capped at 10.0.

    Parameters
    ----------
    kda       : Raw KDA ratio
    win_rate  : Win rate as a percentage (0–100)
    games     : Number of games analysed (proxy for Match_Frequency)
    country   : ISO-3166-1 alpha-2 country code (e.g. "KR", "IN")
    nickname  : Player display name (for output labelling)
    role      : Player role (for output labelling)
    source    : Data source name (for output labelling)

    Returns
    -------
    ScoredPlayer namedtuple with all intermediate values.
    """
    kda_n  = _norm_kda(_safe(kda, 0, 0, KDA_CAP))
    wr_n   = _norm_win_rate(win_rate)
    mf_n   = _norm_match_frequency(games)

    raw    = (kda_n * W_KDA) + (wr_n * W_WIN_RATE) + (mf_n * W_MATCH_FREQUENCY)
    mult   = REGIONAL_MULTIPLIERS.get(country.upper(), _DEFAULT_MULTIPLIER)
    final  = min(round(raw * mult, 4), 10.0)

    return ScoredPlayer(
        nickname        = nickname,
        country         = country.upper(),
        role            = role,
        kda             = round(_safe(kda), 4),
        win_rate        = round(_safe(win_rate), 4),
        games_analyzed  = int(_safe(games, 0)),
        kda_norm        = round(kda_n, 4),
        win_rate_norm   = round(wr_n, 4),
        match_freq_norm = round(mf_n, 4),
        raw_score       = round(raw, 4),
        difficulty_mult = mult,
        final_score     = final,
        source          = source,
    )


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorised Rookie Plan scoring for a full DataFrame.

    Expected columns (optional columns fall back to 0 / "XX"):
        nickname, country, role, _source,
        stats.kda | kda,
        stats.win_rate | win_rate,
        stats.games_analyzed | games_analyzed

    Returns a new DataFrame with all ScoredPlayer fields plus:
        global_rank   (1-based rank by final_score descending)

    The function is fully vectorised via pandas arithmetic — no Python-level
    loop over rows.
    """
    work = df.copy()

    # ── Flatten nested stats dict if present ─────────────────────────────────
    if "stats" in work.columns:
        stats_df = work["stats"].apply(
            lambda s: s if isinstance(s, dict) else {}
        ).apply(pd.Series)
        for col in ("kda", "win_rate", "games_analyzed"):
            if col not in work.columns and col in stats_df.columns:
                work[col] = stats_df[col]

    # ── Safe coercion ─────────────────────────────────────────────────────────
    work["kda"]            = pd.to_numeric(work.get("kda", 0),            errors="coerce").fillna(0.0).clip(0, KDA_CAP)
    work["win_rate"]       = pd.to_numeric(work.get("win_rate", 0),       errors="coerce").fillna(0.0).clip(0, WIN_RATE_CAP)
    work["games_analyzed"] = pd.to_numeric(work.get("games_analyzed", 0), errors="coerce").fillna(0.0).clip(0, GAMES_CAP)
    work["country"]        = work.get("country", pd.Series(["XX"] * len(work))).fillna("XX").str.upper()

    # ── Normalisation (vectorised) ────────────────────────────────────────────
    work["kda_norm"]        = (work["kda"]            / KDA_CAP        * 10.0).round(4)
    work["win_rate_norm"]   = (work["win_rate"]       / WIN_RATE_CAP   * 10.0).round(4)
    work["match_freq_norm"] = (work["games_analyzed"] / GAMES_CAP      * 10.0).round(4)

    # ── Rookie Plan score (vectorised) ────────────────────────────────────────
    work["raw_score"] = (
        work["kda_norm"]        * W_KDA +
        work["win_rate_norm"]   * W_WIN_RATE +
        work["match_freq_norm"] * W_MATCH_FREQUENCY
    ).round(4)

    # ── Regional multiplier (vectorised via map) ──────────────────────────────
    work["difficulty_mult"] = work["country"].map(
        lambda c: REGIONAL_MULTIPLIERS.get(c, _DEFAULT_MULTIPLIER)
    )

    # ── Final score, capped at 10 ─────────────────────────────────────────────
    work["final_score"] = (work["raw_score"] * work["difficulty_mult"]).clip(upper=10.0).round(4)

    # ── Global rank ───────────────────────────────────────────────────────────
    work["global_rank"] = work["final_score"].rank(method="min", ascending=False).astype(int)

    # ── Column ordering ───────────────────────────────────────────────────────
    priority = [
        "global_rank", "nickname", "country", "role",
        "kda", "win_rate", "games_analyzed",
        "kda_norm", "win_rate_norm", "match_freq_norm",
        "raw_score", "difficulty_mult", "final_score",
        "_source",
    ]
    cols = [c for c in priority if c in work.columns] + [
        c for c in work.columns if c not in priority
    ]

    result = work[cols].sort_values("global_rank").reset_index(drop=True)
    logger.info(
        f"Scoring complete — {len(result)} players ranked. "
        f"Top player: {result.iloc[0]['nickname']}  "
        f"final_score={result.iloc[0]['final_score']:.4f}"
    )
    return result


def rank_players(records: list[dict]) -> pd.DataFrame:
    """
    End-to-end convenience function:
        1. Convert records list → DataFrame
        2. Translate esports terms (role, rank, team)
        3. Score and rank via score_dataframe()

    Parameters
    ----------
    records : list of player dicts (bronze or master_rookie format)

    Returns
    -------
    pd.DataFrame — ranked scoring table, ready for display or export
    """
    if not records:
        logger.warning("rank_players called with empty records list")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = translate_dataframe(df)
    ranked = score_dataframe(df)

    logger.info(f"rank_players done — {len(ranked)} players in final ranking")
    return ranked


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CLI / DEMO
# ══════════════════════════════════════════════════════════════════════════════

def _print_ranking(df: pd.DataFrame) -> None:
    """Pretty-print a scoring DataFrame to stdout."""
    display_cols = [
        "global_rank", "nickname", "country", "role",
        "kda", "win_rate", "games_analyzed",
        "raw_score", "difficulty_mult", "final_score",
    ]
    cols = [c for c in display_cols if c in df.columns]
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 160)
    print(df[cols].to_string(index=False))


def _demo_translation() -> None:
    """Print a translation table showing the technical mapping in action."""
    print("\n-- Technical Mapping Demo ------------------------------------------")
    samples = [
        ("打野",      "zh-CN"),
        ("射手",      "zh-CN"),
        ("미드",      "ko"),
        ("정글",      "ko"),
        ("원딜",      "ko"),
        ("ジャングル", "ja"),
        ("ADC",       "ja"),
        ("एडीसी",    "hi"),
        ("जंगलर",    "hi"),
        ("จังเกิล",   "th"),
        ("xạ thủ",   "vi"),
        ("đi rừng",  "vi"),
        ("中单",      "zh-CN"),
        ("輔助",      "zh-TW"),
        ("서포터",    "ko"),
        ("サポート",  "ja"),
        ("Tank",      "ko"),  # ASCII passthrough
    ]
    print(f"  {'Term':<22} {'Lang':<8} → {'Canonical'}")
    print(f"  {'-'*22} {'-'*8}   {'-'*20}")
    for term, lang in samples:
        canonical = translate_esports_term(term, lang)
        tier = "DICT" if term.strip() in TECHNICAL_MAPPING.get(lang, {}) else "API/PASS"
        print(f"  {term:<22} {lang:<8} → {canonical:<20}  [{tier}]")


def _demo_scoring(master_path: str = "master_rookie.json") -> None:
    """Load master_rookie.json and print the Rookie Plan ranking."""
    import json, pathlib

    path = pathlib.Path(master_path)
    if not path.exists():
        logger.warning(f"{master_path} not found — using synthetic demo data")
        records = [
            {"nickname": "Faker",      "country": "KR", "role": "Mid",     "_source": "dakgg",   "stats": {"kda": 6.1, "win_rate": 71.0, "games_analyzed": 100}},
            {"nickname": "Chovy",      "country": "KR", "role": "Mid",     "_source": "dakgg",   "stats": {"kda": 7.3, "win_rate": 68.5, "games_analyzed": 95}},
            {"nickname": "Knight",     "country": "CN", "role": "中单",    "_source": "wanplus", "stats": {"kda": 5.2, "win_rate": 58.0, "games_analyzed": 90}},
            {"nickname": "ShowMaker",  "country": "KR", "role": "Mid",     "_source": "opgg_kr", "stats": {"kda": 5.8, "win_rate": 65.2, "games_analyzed": 85}},
            {"nickname": "Keria",      "country": "KR", "role": "Support", "_source": "opgg_kr", "stats": {"kda": 4.9, "win_rate": 70.1, "games_analyzed": 78}},
            {"nickname": "JackeyLove", "country": "CN", "role": "射手",    "_source": "wanplus", "stats": {"kda": 4.8, "win_rate": 62.5, "games_analyzed": 80}},
        ]
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("players", [])
        logger.info(f"Loaded {len(records)} players from {master_path}")

    print("\n-- Rookie Plan Ranking ---------------------------------------------")
    print(f"  Formula: Score = (KDA×{W_KDA}) + (WinRate×{W_WIN_RATE}) + (MatchFreq×{W_MATCH_FREQUENCY})")
    print(f"  Multipliers: KR×{REGIONAL_MULTIPLIERS['KR']}  IN×{REGIONAL_MULTIPLIERS['IN']}  others×{_DEFAULT_MULTIPLIER}")
    print()

    ranked = rank_players(records)
    _print_ranking(ranked)


if __name__ == "__main__":
    import sys

    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> │ <level>{level:<8}</level> │ {message}", colorize=True, level="DEBUG")

    _demo_translation()
    _demo_scoring()
