import MetaTrader5 as mt5
import pandas as pd

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
BARS = 100

print("=" * 60)
print("HAZEM AI NEWS TRADER - MARKET DATA")
print("=" * 60)

# Connect to MT5
if not mt5.initialize():
    print("❌ MT5 connection failed")
    print("Error:", mt5.last_error())
    quit()

print("✅ MT5 connected")

# Make sure symbol is available
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
    print("❌ Could not get market data")
    print("Error:", mt5.last_error())
    mt5.shutdown()
    quit()

# Convert to DataFrame
df = pd.DataFrame(rates)

# Convert timestamp
df["time"] = pd.to_datetime(df["time"], unit="s")

print()
print("📊 MARKET DATA")
print("-" * 60)

print("Symbol:", SYMBOL)
print("Timeframe: M5")
print("Candles:", len(df))

print()
print("LAST 10 CANDLES")
print("-" * 60)

print(
    df[
        ["time", "open", "high", "low", "close", "tick_volume"]
    ].tail(10).to_string(index=False)
)

# Current price
tick = mt5.symbol_info_tick(SYMBOL)

if tick:
    print()
    print("CURRENT PRICE")
    print("-" * 60)
    print("Bid:", tick.bid)
    print("Ask:", tick.ask)
    print("Spread:", round(tick.ask - tick.bid, 2))

print()
print("✅ MARKET DATA SUCCESSFULLY RECEIVED")
print("=" * 60)

mt5.shutdown()