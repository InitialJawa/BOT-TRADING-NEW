"""Check current positions and state"""
import MetaTrader5 as mt5
import json
from datetime import datetime
from pathlib import Path

mt5.initialize()
info = mt5.account_info()
print(f"Balance: ${info.balance:.2f} | Equity: ${info.equity:.2f} | Profit: ${info.profit:.2f}")
print(f"Margin: ${info.margin:.2f} | Free: ${info.margin_free:.2f}")
print()

for sym in ["XAUUSDm", "US30m", "JP225m"]:
    pos = mt5.positions_get(symbol=sym)
    if pos and len(pos) > 0:
        p = pos[0]
        side = "BUY" if p.type == 0 else "SELL"
        print(f"{sym:12} {'OPEN':>4} {side:>4} Vol={p.volume:.2f} Entry={p.price_open:.2f} "
              f"SL={p.sl:.2f} TP={p.tp:.2f} Price={p.price_current:.2f} "
              f"Profit={p.profit:.2f}")
    else:
        print(f"{sym:12} NO POSITION")

    # Show state
    sp = Path(f"state_{sym}.json")
    if sp.exists():
        with open(sp) as f:
            s = json.load(f)
        print(f"           State: loss_streak={s.get('consecutive_losses',0)} "
              f"daily_pnl={s.get('daily_pnl',0):.2f}")
    print()

mt5.shutdown()
