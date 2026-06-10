"""Cek spread & availability pair tambahan"""
import MetaTrader5 as mt5
mt5.initialize()

pairs = ["US30m", "GER40m", "JP225m", "UK100m", "US30", "GER40", "JP225", "UK100",
         "US30cash", "DE40", "UK100", "JP225"]

print(f"{'Symbol':<12} {'Spread':>8} {'TickV':>8} {'M1 ok?':>7} {'Price':>10}")
print("-" * 48)
for sym in pairs:
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    if info is None: continue
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 3)
    m1_ok = r is not None and len(r) > 0
    print(f"{sym:<12} {info.spread:>8} {info.trade_tick_value:>8.2f} {'YES' if m1_ok else 'no':>7} {info.bid:>10.2f}")

mt5.shutdown()
