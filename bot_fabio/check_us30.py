import MetaTrader5 as mt5
from datetime import datetime, timedelta
mt5.initialize()

yesterday = datetime.now() - timedelta(days=1)
deals = mt5.history_deals_get(yesterday, datetime.now())
us30 = [d for d in deals if d.magic == 25062027 and d.entry == 1]

wins = [d for d in us30 if d.profit > 0]
losses = [d for d in us30 if d.profit <= 0]
print("US30 PULLBACK:")
print("  Closed:", len(us30))
print("  Wins:", len(wins), "({:.1f}%)".format(len(wins)/len(us30)*100 if us30 else 0))
print("  Losses:", len(losses))
if wins: print("  Avg win: ${:.2f}".format(sum(d.profit for d in wins)/len(wins)))
if losses: print("  Avg loss: ${:.2f}".format(sum(d.profit for d in losses)/len(losses)))
print("  Net: ${:.2f}".format(sum(d.profit for d in us30)))

si = mt5.symbol_info("US30m")
tick = mt5.symbol_info_tick("US30m")
spread_pts = (tick.ask - tick.bid) / si.trade_tick_size
print("\nUS30m spread: {:.1f} pts".format(spread_pts))

rates = mt5.copy_rates_from_pos("US30m", mt5.TIMEFRAME_M5, 0, 20)
if rates:
    atr = sum(abs(r[2]-r[3]) for r in rates[-14:]) / 14
    print("US30m ATR M5: {:.2f}".format(atr))
    sl = atr * 0.3
    tp = atr * 0.6
    print("  SL: {:.2f} pts, TP: {:.2f} pts".format(sl, tp))
    print("  SL/spread ratio: {:.1f}x".format(sl / spread_pts if spread_pts > 0 else 999))

# print last few trades
print("\nLAST 10 TRADES:")
for d in us30[-10:]:
    side = "BUY" if d.type in (0, 2) else "SELL"
    print("  {} PnL=${:.2f}".format(side, d.profit))

mt5.shutdown()
