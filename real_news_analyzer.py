import os
import json
import feedparser
from urllib.parse import quote
from dotenv import load_dotenv
from google import genai

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found")
    quit()

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.6-flash"

# ============================================================
# GET REAL NEWS
# ============================================================

query = quote(
    '(gold OR XAUUSD OR "Federal Reserve" OR '
    '"interest rates" OR inflation OR USD OR Trump)'
)

RSS_URL = (
    "https://news.google.com/rss/search?"
    f"q={query}&hl=en-US&gl=US&ceid=US:en"
)

print("=" * 70)
print("HAZEM AI NEWS TRADER - REAL NEWS ANALYZER")
print("=" * 70)

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    print("ERROR: No news received")
    quit()

# Take only latest 10
news_items = feed.entries[:10]

print()
print("NEWS RECEIVED:", len(feed.entries))
print("ANALYZING:", len(news_items))
print("-" * 70)

for i, item in enumerate(news_items, 1):
    print(f"{i}. {item.get('title', 'No title')}")

# ============================================================
# PREPARE NEWS FOR GEMINI
# ============================================================

news_text = ""

for i, item in enumerate(news_items, 1):

    title = item.get("title", "No title")
    published = item.get("published", "Unknown")

    news_text += f"""
NEWS {i}
Title: {title}
Published: {published}
"""

# ============================================================
# GEMINI ANALYSIS
# ============================================================

prompt = f"""
You are a financial news classification engine.

Analyze the following RECENT NEWS HEADLINES for their potential
short-term impact on GOLD / XAUUSD.

Important rules:

1. Analyze the information provided only.
2. Do not invent facts.
3. Consider whether multiple headlines describe the SAME event.
4. Do not simply count bullish or bearish headlines.
5. Consider the likely impact through:
   - US Dollar
   - US Treasury yields
   - Federal Reserve policy
   - interest rates
   - inflation
   - geopolitical risk
   - safe-haven demand
6. If the information is contradictory or insufficient,
   reduce confidence.
7. This is NOT an instruction to execute a trade.

Return ONLY valid JSON.

NEWS:
{news_text}

Use exactly this structure:

{{
    "asset": "XAUUSD",
    "direction": "BULLISH or BEARISH or NEUTRAL",
    "news_score": 0,
    "confidence": 0,
    "time_horizon": "SHORT_TERM or MEDIUM_TERM or UNCLEAR",
    "event_summary": "short summary",
    "reason": "short explanation",
    "key_factors": [
        "factor 1",
        "factor 2",
        "factor 3"
    ]
}}

Scoring:

+100 = extremely bullish for gold
+75  = strongly bullish
+50  = moderately bullish
+25  = slightly bullish
0    = neutral / unclear
-25  = slightly bearish
-50  = moderately bearish
-75  = strongly bearish
-100 = extremely bearish

news_score must be between -100 and +100.

confidence must be between 0 and 100.
"""

print()
print("-" * 70)
print("SENDING NEWS TO GEMINI...")
print("-" * 70)

try:

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    print()
    print("GEMINI RESULT")
    print("-" * 70)
    print(text)

    # ========================================================
    # JSON VALIDATION
    # ========================================================

    try:

        result = json.loads(text)

        print()
        print("=" * 70)
        print("JSON VALIDATION: SUCCESS")
        print("=" * 70)

        print("Asset:", result["asset"])
        print("Direction:", result["direction"])
        print("News Score:", result["news_score"])
        print("Confidence:", result["confidence"])
        print("Time Horizon:", result["time_horizon"])

        print()
        print("Event Summary:")
        print(result["event_summary"])

        print()
        print("Reason:")
        print(result["reason"])

        print()
        print("Key Factors:")

        for factor in result["key_factors"]:
            print("-", factor)

        print()
        print("=" * 70)
        print("REAL NEWS ANALYSIS SUCCESS")
        print("=" * 70)

    except json.JSONDecodeError:

        print()
        print("JSON VALIDATION: FAILED")
        print("Gemini returned non-JSON output.")

except Exception as e:

    print()
    print("GEMINI ERROR:")
    print(type(e).__name__)
    print(str(e))