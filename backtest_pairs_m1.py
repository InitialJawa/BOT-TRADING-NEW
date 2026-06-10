"""Backtest US30, JP225, UK100 — M1 EMA 8/34 Cross"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

mt5.initialize()
SL_M = 0.3; TP_M = 0.6; TRAIL_M = 0.2

def load_data(sym, n=60000):
    mt5.symbol_select(sym, True)
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, n)
    if r is None: return None
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.columns = [c.lower() for c in df.columns]
    c, h, l = df["close"], df["high"], df["low"]
    df["ema8"] = c.ewm(span=8, adjust=False).mean()
    df["ema34"] = c.ewm(span=34, adjust=False).mean()
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=14, adjust=False).mean()
    df.dropna(inplace=True)
    return df

pairs = [
    ("US30m",  "US30",  10),
    ("JP225m", "JP225",  1),  # will check multiplier
    ("UK100m", "UK100",  1),  # will check multiplier
]

for sym, label, mult in pairs:
    info = mt5.symbol_info(sym)
    if info:
        print(f"{label:12} tick_val={info.trade_tick_value}  contract={info.trade_contract_size}  lot={info.volume_min}-{info.volume_max}")
        mult = max(1, round(info.trade_tick_value / 0.01))
        print(f"{'':>12} => multiplier = {mult} (${mult*0.01}/point per 0.01lot)")

print()

data = []
for sym, label, _ in pairs:
    df = load_data(sym, 60000)
    if df is None: print(f"{label}: NO DATA"); continue
    days = round((df.index[-1] - df.index[0]).total_seconds() / 86400, 0)

    info = mt5.symbol_info(sym)
    mult = max(1, round(info.trade_tick_value / 0.01))

    trades = []
    active = None
    for idx in range(1, len(df)):
        bar = df.iloc[idx]; prev = df.iloc[idx-1]
        sig = None
        if prev["ema8"] <= prev["ema34"] and bar["ema8"] > bar["ema34"]: sig = "BUY"
        elif prev["ema8"] >= prev["ema34"] and bar["ema8"] < bar["ema34"]: sig = "SELL"
        if sig:
            sl = round(bar["close"] - bar["atr"] * SL_M, 2) if sig == "BUY" else round(bar["close"] + bar["atr"] * SL_M, 2)
            tp = round(bar["close"] + bar["atr"] * TP_M, 2) if sig == "BUY" else round(bar["close"] - bar["atr"] * TP_M, 2)
            active = {"side": sig, "entry": bar["close"], "sl": sl, "tp": tp, "atr": bar["atr"]}
        if active:
            if TRAIL_M > 0:
                tl = active["atr"] * TRAIL_M
                if active["side"] == "BUY":
                    pf = bar["close"] - active["entry"]
                    if pf > tl and bar["close"] - tl > active["sl"]: active["sl"] = bar["close"] - tl
                else:
                    pf = active["entry"] - bar["close"]
                    if pf > tl and bar["close"] + tl < active["sl"]: active["sl"] = bar["close"] + tl
            ep = None
            if active["side"] == "BUY":
                if bar["high"] >= active["tp"]: ep = active["tp"]
                elif bar["low"] <= active["sl"]: ep = active["sl"]
            else:
                if bar["low"] <= active["tp"]: ep = active["tp"]
                elif bar["high"] >= active["sl"]: ep = active["sl"]
            if ep:
                pp = (ep - active["entry"]) if active["side"] == "BUY" else (active["entry"] - ep)
                pnl = pp * 0.01 * mult
                trades.append(pnl)
                active = None

    wins = sum(1 for p in trades if p > 0)
    gp = sum(p for p in trades if p > 0)
    gl = abs(sum(p for p in trades if p < 0))
    pf = round(gp/gl, 2) if gl else 0
    net = round(sum(trades), 2)
    avg_atr = round(np.mean([df.iloc[i]["atr"] for i in range(100, len(df))]), 2)
    data.append((label, len(trades), round(len(trades)/days, 1), round(wins/len(trades)*100 if trades else 0),
                 pf, net, avg_atr, days, mult))

mt5.shutdown()

print(f"{'='*75}")
print(f"  M1 EMA 8/34 CROSS — 0.01 LOT TETAP")
print(f"{'='*75}")
print(f"  {'Pair':<10} {'Trades':>7} {'/hari':>6} {'WR%':>5} {'PF':>5} {'Net$':>9} {'AvgATR':>7} {'Periode':>8} {'Mult':>5}")
print(f"  {'-'*65}")
for d in data:
    print(f"  {d[0]:<10} {d[1]:>7} {d[2]:>5.1f} {d[3]:>4.0f}% {d[4]:>5.2f} ${d[5]:>+7.2f} {d[6]:>7.2f} {d[7]:>5.0f}hr {d[8]:>5}")

# Proyeksi untuk $300
print(f"\n{'='*75}")
print(f"  PROYEKSI MODAL $300 — LOT 0.05")
print(f"{'='*75}")
print(f"  {'Pair':<10} {'/hari':>8} {'/bln':>10} {'Risk%':>8} {'DD%':>8}")
print(f"  {'-'*45}")
for d in data:
    label = d[0]; trades_n = d[1]; days = d[7]; net = d[5]
    per_day_01 = net / days
    per_month_01 = per_day_01 * 30
    proy_month = per_month_01 * 5  # lot 0.05 vs 0.01
    risk_pct = round(proy_month / 300 * 100, 0)
    print(f"  {label:<10} ${per_day_01*5:>6.2f} ${proy_month:>+8.2f} {risk_pct:>6.0f}% {'lihat DD':>8}")
