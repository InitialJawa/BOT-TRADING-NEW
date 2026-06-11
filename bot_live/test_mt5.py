"""Quick test: verify MT5 data for M1 + M5"""
import MetaTrader5 as mt5
mt5.initialize()
for sym in ["XAUUSDm", "US30m"]:
    mt5.symbol_select(sym, True)
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 10)
    r5 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, 10)
    ok1 = r is not None and len(r) > 0
    ok5 = r5 is not None and len(r5) > 0
    print(f"{sym:12} M1: {len(r) if ok1 else 0} bars | price={r[-1][4] if ok1 else 'N/A'}")
    print(f"{sym:12} M5: {len(r5) if ok5 else 0} bars | price={r5[-1][4] if ok5 else 'N/A'}")
    print()
mt5.shutdown()
