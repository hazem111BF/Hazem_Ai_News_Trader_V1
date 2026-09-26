# -*- coding: utf-8 -*-
"""
HAZEM AI NEWS TRADER V1 - HARDENED NEWS ANALYZER
Purpose:
    - Fetch fresh financial news for XAUUSD.
    - Send only filtered news to Gemini.
    - Use structured JSON output when supported.
    - Retry transient Gemini failures.
    - Automatically fall back across available Gemini Flash models.
    - Validate the returned analysis before printing it for signal_engine.py.
    - Never expose GEMINI_API_KEY.

Compatibility:
    Existing signal_engine.py can continue to call:
        python -u news_analyzer.py

Required packages:
    pip install google-genai python-dotenv feedparser
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote

import feedparser
from dotenv import load_dotenv
from google import genai

try:
    from google.genai import types
except Exception:
    types = None


# ============================================================
# CONFIG
# ============================================================

ASSET = "XAUUSD"
MAX_NEWS = 10
MAX_NEWS_AGE_HOURS = 12

# Current stable Gemini Flash family, ordered by preferred use.
# The user's API key/account may not have every model enabled,
# so the program automatically falls through to the next one.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

# Retries per model for transient server/rate-limit errors.
RETRIES_PER_MODEL = 2
BASE_RETRY_DELAY = 3.0
MAX_RETRY_DELAY = 20.0

# Do not retry permanent request errors indefinitely.
TRANSIENT_MARKERS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
    "TIMEOUT",
    "TIMED OUT",
)

# Models that are explicitly unavailable to a key should be skipped
# immediately instead of wasting retries.
PERMANENT_MODEL_MARKERS = (
    "404",
    "NOT_FOUND",
    "not found",
    "not available to new users",
    "MODEL_NOT_FOUND",
)

QUERY = (
    '("gold price" OR XAUUSD OR "gold bullion" OR '
    '"Federal Reserve" OR Fed OR "interest rates" OR inflation OR '
    '"US dollar" OR USD OR "Treasury yields" OR "Treasury yield")'
)

RSS_URL = (
    "https://news.google.com/rss/search?"
    + f"q={quote(QUERY)}&hl=en-US&gl=US&ceid=US:en"
)

FINANCIAL_KEYWORDS = [
    "gold", "xau", "fed", "federal reserve", "interest rate",
    "interest rates", "inflation", "cpi", "ppi", "dollar", "usd",
    "treasury", "yield", "bond", "central bank", "monetary policy",
    "rate cut", "rate hike", "jobs", "employment", "payroll",
    "nonfarm", "geopolitical", "war", "tariff", "trade", "oil",
    "crude", "fomc", "powell", "safe haven"
]

IRRELEVANT_KEYWORDS = [
    "hockey", "nhl", "basketball", "nba", "football", "soccer",
    "baseball", "scrimmage", "roster", "tournament", "athletics",
    "paladin", "cyclones", "university"
]

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "direction": {
            "type": "string",
            "enum": ["BULLISH", "BEARISH", "NEUTRAL"],
        },
        "news_score": {"type": "integer"},
        "confidence": {"type": "integer"},
        "time_horizon": {
            "type": "string",
            "enum": ["SHORT_TERM", "MEDIUM_TERM", "UNCLEAR"],
        },
        "reason": {"type": "string"},
        "key_factors": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "asset",
        "direction",
        "news_score",
        "confidence",
        "time_horizon",
        "reason",
        "key_factors",
    ],
}


# ============================================================
# SAFE OUTPUT / LOGGING
# ============================================================

def log(message=""):
    print(message, flush=True)


def error_message(exc):
    """Return an error string without leaking API keys."""
    text = str(exc)
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key:
        text = text.replace(api_key, "***REDACTED***")
    return text


def is_transient_error(exc):
    text = error_message(exc).upper()
    return any(marker.upper() in text for marker in TRANSIENT_MARKERS)


def is_permanent_model_error(exc):
    text = error_message(exc)
    return any(marker in text for marker in PERMANENT_MODEL_MARKERS)


# ============================================================
# GEMINI CLIENT
# ============================================================

def create_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        log("ERROR: GEMINI_API_KEY was not found in .env")
        log("Make sure .env contains:")
        log("GEMINI_API_KEY=YOUR_KEY")
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        log("ERROR: Could not initialize Gemini client.")
        log(error_message(exc))
        return None


# ============================================================
# NEWS FETCHING
# ============================================================

def parse_entry_datetime(item):
    parsed = item.get("published_parsed") or item.get("updated_parsed")
    if not parsed:
        return None

    try:
        return datetime(
            parsed.tm_year,
            parsed.tm_mon,
            parsed.tm_mday,
            parsed.tm_hour,
            parsed.tm_min,
            parsed.tm_sec,
            tzinfo=timezone.utc,
        )
    except Exception:
        return None


def freshness_weight(age_hours):
    if age_hours <= 0.25:
        return 1.00
    if age_hours <= 1:
        return 0.90
    if age_hours <= 3:
        return 0.70
    if age_hours <= 6:
        return 0.40
    return 0.20


def fetch_relevant_news():
    log("=" * 78)
    log("HAZEM AI NEWS TRADER V1 - HARDENED NEWS PIPELINE")
    log("=" * 78)
    log("Fetching Google News RSS...")

    try:
        feed = feedparser.parse(RSS_URL)
    except Exception as exc:
        raise RuntimeError(f"News feed error: {error_message(exc)}") from exc

    if not feed.entries:
        raise RuntimeError("No news entries were received from Google News RSS.")

    now = datetime.now(timezone.utc)
    seen = set()
    filtered = []

    for item in feed.entries:
        title = str(item.get("title", "")).strip()
        if not title:
            continue

        low = title.lower()

        if any(word in low for word in IRRELEVANT_KEYWORDS):
            continue

        if not any(word in low for word in FINANCIAL_KEYWORDS):
            continue

        normalized = re.sub(r"\s+", " ", low)
        if normalized in seen:
            continue
        seen.add(normalized)

        published = parse_entry_datetime(item)
        if not published:
            continue

        age_hours = (now - published).total_seconds() / 3600.0

        # Ignore future-dated RSS entries caused by clock/feed anomalies.
        if age_hours < -(5 / 60):
            continue

        if age_hours > MAX_NEWS_AGE_HOURS:
            continue

        filtered.append(
            {
                "title": title,
                "published": published,
                "age_hours": age_hours,
                "freshness_weight": freshness_weight(age_hours),
                "link": str(item.get("link", "")),
            }
        )

    filtered.sort(key=lambda row: row["age_hours"])
    filtered = filtered[:MAX_NEWS]

    log(f"TOTAL NEWS RECEIVED: {len(feed.entries)}")
    log(f"FRESH FINANCIAL NEWS SELECTED: {len(filtered)}")

    if not filtered:
        raise RuntimeError(
            "No recent relevant financial news passed the safety filters."
        )

    log("\n" + "-" * 78)
    log("SELECTED NEWS")
    log("-" * 78)

    for i, item in enumerate(filtered, 1):
        minutes = max(0, round(item["age_hours"] * 60))
        log(f"{i}. {item['title']}")
        log(f"   Age: {minutes} minutes")
        log(f"   Freshness weight: {item['freshness_weight']:.2f}")
        log(f"   Published UTC: {item['published'].isoformat()}")
        log(f"   Link: {item['link']}")

    return filtered


# ============================================================
# PROMPT
# ============================================================

def build_prompt(news_items):
    blocks = []

    for i, item in enumerate(news_items, 1):
        minutes = max(0, round(item["age_hours"] * 60))
        blocks.append(
            f"NEWS {i}\n"
            f"Title: {item['title']}\n"
            f"Age minutes: {minutes}\n"
            f"Freshness weight: {item['freshness_weight']:.2f}\n"
            f"Published UTC: {item['published'].isoformat()}\n"
            f"Source URL: {item['link']}\n"
        )

    news_text = "\n".join(blocks)

    return f"""
You are the news-classification engine inside an XAUUSD market-analysis system.

Analyze ONLY the supplied recent news. Do not use outside facts that are not
present in the supplied headlines.

Objective:
Estimate the short-term directional pressure that the supplied news creates
for GOLD / XAUUSD.

Strict rules:
1. Never invent facts, events, prices, sources, or dates.
2. Do not treat a headline about a past price move as proof that the move will continue.
3. Multiple headlines can describe the same event. Do not double-count them.
4. Give higher importance to Federal Reserve/FOMC, interest rates, inflation,
   USD, Treasury yields, gold-specific fundamentals, and major geopolitical risk.
5. Fresh news receives more weight than old news.
6. If evidence conflicts, is weak, or is insufficient, use NEUTRAL and lower confidence.
7. news_score must be an integer from -100 to +100.
8. confidence must be an integer from 0 to 100.
9. This is classification for a demo/alert system, not financial advice.
10. Return ONLY one JSON object. No Markdown. No explanation outside JSON.

Scoring guide:
+90 to +100 = extremely strong bullish news pressure
+70 to +89  = strong bullish
+40 to +69  = moderate bullish
+20 to +39  = weak bullish
-19 to +19  = neutral / unclear
-20 to -39  = weak bearish
-40 to -69  = moderate bearish
-70 to -89  = strong bearish
-90 to -100 = extremely strong bearish

Required JSON:
{{
  "asset": "XAUUSD",
  "direction": "BULLISH",
  "news_score": 0,
  "confidence": 0,
  "time_horizon": "SHORT_TERM",
  "reason": "brief evidence-based reason",
  "key_factors": ["factor 1", "factor 2", "factor 3"]
}}

Allowed:
direction = BULLISH | BEARISH | NEUTRAL
time_horizon = SHORT_TERM | MEDIUM_TERM | UNCLEAR

SUPPLIED NEWS:
{news_text}
""".strip()


# ============================================================
# GEMINI CALL
# ============================================================

def build_config():
    """
    Structured JSON is requested when the installed google-genai SDK
    supports the config object. If not, the program falls back to a
    plain chat request and performs strict local JSON validation.
    """
    if types is None:
        return None

    try:
        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JSON_SCHEMA,
            temperature=0.0,
        )
    except Exception:
        return None


def send_to_gemini(client, model, prompt):
    """
    One logical Gemini request.
    Uses the Chat API to avoid the automatic-function-calling warning path.
    """
    config = build_config()

    if config is not None:
        chat = client.chats.create(model=model, config=config)
    else:
        chat = client.chats.create(model=model)

    response = chat.send_message(prompt)
    text = getattr(response, "text", None)

    if not text or not text.strip():
        raise RuntimeError(f"Gemini returned an empty response for {model}.")

    return text.strip()


# ============================================================
# JSON EXTRACTION / VALIDATION
# ============================================================

def strip_code_fences(text):
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def parse_json_object(text):
    text = strip_code_fences(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Controlled recovery only: extract the outermost JSON object.
        start = text.find("{")
        end = text.rfind("}")

        if start < 0 or end <= start:
            raise ValueError("Gemini response does not contain a JSON object.")

        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON returned by Gemini: {exc}") from exc


def validate_result(result):
    if not isinstance(result, dict):
        raise ValueError("Gemini result is not a JSON object.")

    required = [
        "asset",
        "direction",
        "news_score",
        "confidence",
        "time_horizon",
        "reason",
        "key_factors",
    ]

    missing = [field for field in required if field not in result]
    if missing:
        raise ValueError(f"Missing required field: {missing[0]}")

    if result["asset"] != ASSET:
        raise ValueError(f"Invalid asset: {result['asset']}")

    if result["direction"] not in {"BULLISH", "BEARISH", "NEUTRAL"}:
        raise ValueError(f"Invalid direction: {result['direction']}")

    if result["time_horizon"] not in {
        "SHORT_TERM",
        "MEDIUM_TERM",
        "UNCLEAR",
    }:
        raise ValueError(f"Invalid time_horizon: {result['time_horizon']}")

    try:
        score = int(result["news_score"])
        confidence = int(result["confidence"])
    except Exception as exc:
        raise ValueError("news_score/confidence must be integers.") from exc

    if not -100 <= score <= 100:
        raise ValueError("news_score is outside -100..100.")

    if not 0 <= confidence <= 100:
        raise ValueError("confidence is outside 0..100.")

    if not isinstance(result["reason"], str) or not result["reason"].strip():
        raise ValueError("reason must be a non-empty string.")

    if not isinstance(result["key_factors"], list):
        raise ValueError("key_factors must be a list.")

    if len(result["key_factors"]) > 10:
        raise ValueError("Too many key_factors.")

    cleaned_factors = []
    for factor in result["key_factors"]:
        if not isinstance(factor, str):
            raise ValueError("Every key_factor must be a string.")
        factor = factor.strip()
        if factor:
            cleaned_factors.append(factor[:300])

    result["news_score"] = score
    result["confidence"] = confidence
    result["reason"] = result["reason"].strip()[:1000]
    result["key_factors"] = cleaned_factors

    # Consistency guard: a very confident neutral result is allowed,
    # but an extremely high score with extremely low confidence is not.
    if abs(score) >= 80 and confidence < 35:
        raise ValueError(
            "Inconsistent result: extreme news_score with very low confidence."
        )

    return result


# ============================================================
# MODEL FAILOVER
# ============================================================

def analyze_with_failover(client, prompt):
    failures = []

    for model in MODELS:
        log("\n" + "=" * 78)
        log(f"TRYING GEMINI MODEL: {model}")
        log("=" * 78)

        for attempt in range(1, RETRIES_PER_MODEL + 1):
            log(f"Attempt {attempt}/{RETRIES_PER_MODEL}")

            try:
                raw = send_to_gemini(client, model, prompt)
                result = validate_result(parse_json_object(raw))

                log(f"SUCCESS: {model}")
                return result, model, failures

            except Exception as exc:
                message = error_message(exc)
                failures.append(
                    {
                        "model": model,
                        "attempt": attempt,
                        "error": message[:500],
                    }
                )

                log(f"Gemini error: {message}")

                if is_permanent_model_error(exc):
                    log("Model appears unavailable for this API key. Skipping it.")
                    break

                if is_transient_error(exc) and attempt < RETRIES_PER_MODEL:
                    delay = min(
                        BASE_RETRY_DELAY * (2 ** (attempt - 1)),
                        MAX_RETRY_DELAY,
                    )
                    log(f"Temporary service error. Waiting {delay:.1f}s...")
                    time.sleep(delay)
                    continue

                # For malformed output or non-transient request errors,
                # move to the next model instead of hammering one model.
                break

    return None, None, failures


# ============================================================
# MAIN
# ============================================================

def main():
    client = create_client()
    if client is None:
        return 2

    try:
        news_items = fetch_relevant_news()
        prompt = build_prompt(news_items)

        result, model, failures = analyze_with_failover(client, prompt)

        if result is None:
            log("\n" + "=" * 78)
            log("GEMINI PIPELINE FAILED")
            log("=" * 78)
            log("All configured Gemini models failed.")
            log("The program did NOT create a fake signal.")
            log("This is an important safety behavior for a trading system.")

            for failure in failures[-10:]:
                log(
                    f"- {failure['model']} attempt {failure['attempt']}: "
                    f"{failure['error']}"
                )

            return 1

        # Print a single clean JSON object too, so signal_engine.py can
        # extract it exactly as it did with the previous analyzer.
        output = {
            **result,
            "model_used": model,
            "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
            "news_count": len(news_items),
            "pipeline_status": "SUCCESS",
        }

        log("\n" + "=" * 78)
        log("JSON VALIDATION: SUCCESS")
        log("=" * 78)
        log(f"Model Used: {model}")
        log(f"Asset: {output['asset']}")
        log(f"Direction: {output['direction']}")
        log(f"News Score: {output['news_score']}")
        log(f"Confidence: {output['confidence']}")
        log(f"Time Horizon: {output['time_horizon']}")
        log(f"News Count: {output['news_count']}")
        log("\nReason:")
        log(output["reason"])
        log("\nKey Factors:")
        for factor in output["key_factors"]:
            log(f"- {factor}")

        log("\nFINAL JSON:")
        log(json.dumps(output, ensure_ascii=False))

        log("\n" + "=" * 78)
        log("FRESH NEWS ANALYSIS SUCCESS")
        log("=" * 78)

        return 0

    except Exception as exc:
        log("\n" + "=" * 78)
        log("NEWS PIPELINE ERROR")
        log("=" * 78)
        log(error_message(exc))
        log("No trading signal was generated.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
