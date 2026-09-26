import MetaTrader5 as mt5
from datetime import datetime

SYMBOL = "XAUUSD"

print("=" * 50)
print("HAZEM AI NEWS TRADER - MT5 TEST")
print("=" * 50)

if not mt5.initialize():
    print("MT5 CONNECTION FAILED")
    print("Error:", mt5.last_error())
    quit()

print("MT5 CONNECTED")

account = mt5.account_info()

if account is not None:
    print("Account:", account.login)
    print("Server:", account.server)

symbol_info = mt5.symbol_info(SYMBOL)

if symbol_info is None:
    print("Symbol not found:", SYMBOL)
    mt5.shutdown()
    quit()

if not symbol_info.visible:
    mt5.symbol_select(SYMBOL, True)

tick = mt5.symbol_info_tick(SYMBOL)

if tick is None:
    print("Cannot get price for:", SYMBOL)
    print("Error:", mt5.last_error())
    mt5.shutdown()
    quit()

print()
print("GOLD MARKET DATA")
print("-" * 50)
print("Symbol:", SYMBOL)
print("Bid:", tick.bid)
print("Ask:", tick.ask)
print("Spread:", round(tick.ask - tick.bid, 2))
print("Time:", datetime.fromtimestamp(tick.time))

print()
print("SUCCESS - PYTHON CAN READ XAUUSD FROM MT5")
print("=" * 50)

mt5.shutdown()