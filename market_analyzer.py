import MetaTrader5 as mt5
import pandas as pd
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
BARS = 200


def calculate_market_score(df):
    # EMA
    df["ema20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    # ATR
    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["atr"] = atr.average_true_range()

    latest = df.iloc[-1]

    score = 0
    reasons = []

    # -------------------------
    # TREND
    # -------------------------

    if latest["ema20"] > latest["ema50"]:
        score += 30
        reasons.append("EMA20 above EMA50")
    else:
        score -= 30
        reasons.append("EMA20 below EMA50")

    # -------------------------
    # PRICE vs EMA20
    # -------------------------

    if latest["close"] > latest["ema20"]:
        score += 20
        reasons.append("Price above EMA20")
    else:
        score -= 20
        reasons.append("Price below EMA20")

    # -------------------------
    # MOMENTUM
    # -------------------------

    previous_close = df.iloc[-2]["close"]

    if latest["close"] > previous_close:
        score += 15
        reasons.append("Positive short-term momentum")
    else:
        score -= 15
        reasons.append("Negative short-term momentum")

    # -------------------------
    # CANDLE STRENGTH
    # -------------------------

    candle_range = latest["high"] - latest["low"]

    if candle_range > 0:

        candle_body = abs(
            latest["close"] - latest["open"]
        )

        body_ratio = candle_body / candle_range

        if body_ratio >= 0.60:

            if latest["close"] > latest["open"]:
                score += 15
                reasons.append("Strong bullish candle")

            else:
                score -= 15
                reasons.append("Strong bearish candle")

    # Keep score between -100 and +100
    score = max(-100, min(100, score))

    return score, reasons


print("=" * 65)
print("HAZEM AI NEWS TRADER - MARKET ANALYZER")
print("=" * 65)

# Connect
if not mt5.initialize():

    print("❌ MT5 connection failed")
    print("Error:", mt5.last_error())
    quit()

print("✅ MT5 connected")

# Select symbol
if not mt5.symbol_select(SYMBOL, True):

    print("❌ Cannot select", SYMBOL)
    mt5.shutdown()
    quit()

# Get candles
rates = mt5.copy_rates_from_pos(
    SYMBOL,
    TIMEFRAME,
    0,
    BARS
)

if rates is None:

    print("❌ Cannot get market data")
    print("Error:", mt5.last_error())
    mt5.shutdown()
    quit()

# DataFrame
df = pd.DataFrame(rates)

df["time"] = pd.to_datetime(
    df["time"],
    unit="s"
)

print()
print("Symbol:", SYMBOL)
print("Timeframe: M5")
print("Candles:", len(df))

# Calculate score
score, reasons = calculate_market_score(df)

# Current price
tick = mt5.symbol_info_tick(SYMBOL)

print()
print("=" * 65)
print("MARKET ANALYSIS")
print("=" * 65)

print("Current Bid:", tick.bid)
print("Current Ask:", tick.ask)
print("Spread:", round(tick.ask - tick.bid, 2))

print()
print("EMA20:", round(df.iloc[-1]["ema20"], 2))
print("EMA50:", round(df.iloc[-1]["ema50"], 2))
print("ATR:", round(df.iloc[-1]["atr"], 2))

print()
print("MARKET SCORE:", score)

print()
print("REASONS:")

for reason in reasons:
    print("-", reason)

print()
print("=" * 65)

if score >= 60:
    print("🟢 MARKET BIAS: BULLISH")

elif score <= -60:
    print("🔴 MARKET BIAS: BEARISH")

else:
    print("⚪ MARKET BIAS: NEUTRAL")

print("=" * 65)

mt5.shutdown()