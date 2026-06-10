"""Test HIGH FREQUENCY strategies"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

mt5.initialize()
SL_M = 0.3; TP_M = 0.6; TRAIL_M = 0.2

def load(sym, n=50000):
    mt5.symbol_select(sym, True)
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, n)
    if r is None: return None
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.columns = [c.lower() for c in df.columns]
    c, h, l = df["close"], df["high"], df["low"]
    df["ema8"] = c.ewm(span=8, adjust=False).mean()
    df["ema34"] = c.ewm(span=34, adjust=False).mean()
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=14, adjust=False).mean()
    d = c.diff()
    g = d.clip(lower=0).ewm(span=7, adjust=False).mean()
    ls = (-d.clip(upper=0)).ewm(span=7, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + g / ls.replace(0, np.nan)))
    df["mom"] = c.pct_change(3)
    df.dropna(inplace=True)
    return df

strategies = ["EMA_CROSS", "TREND_RE", "PULLBACK", "MOMENTUM"]

def run_bt(sym, label, mult, strat):
    df = load(sym)
    if df is None: return
    days = round((df.index[-1] - df.index[0]).total_seconds() / 86400, 0)
    trades = []; active = None; cons_l = 0

    for idx in range(1, len(df)):
        bar = df.iloc[idx]; prev = df.iloc[idx-1]
        if cons_l >= 10: continue
        tu = bar["ema8"] > bar["ema34"]; td = bar["ema8"] < bar["ema34"]

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
                if pnl < 0: cons_l += 1
                else: cons_l = 0
                active = None
                # TREND_RE: re-enter on same bar if stopped out
                if strat == "TREND_RE" and pnl < 0:
                    sig = None
                    if tu: sig = "BUY"
                    elif td: sig = "SELL"
                    if sig:
                        sl = round(bar["close"] - bar["atr"] * SL_M, 2) if sig == "BUY" else round(bar["close"] + bar["atr"] * SL_M, 2)
                        tp = round(bar["close"] + bar["atr"] * TP_M, 2) if sig == "BUY" else round(bar["close"] - bar["atr"] * TP_M, 2)
                        active = {"side": sig, "entry": bar["close"], "sl": sl, "tp": tp, "atr": bar["atr"]}
                continue
            else: continue

        sig = None
        if strat == "EMA_CROSS":
            if prev["ema8"] <= prev["ema34"] and bar["ema8"] > bar["ema34"]: sig = "BUY"
            elif prev["ema8"] >= prev["ema34"] and bar["ema8"] < bar["ema34"]: sig = "SELL"
        elif strat == "TREND_RE":
            if tu: sig = "BUY"
            elif td: sig = "SELL"
        elif strat == "PULLBACK":
            if tu and bar["low"] <= bar["ema8"] and bar["close"] > bar["ema8"]: sig = "BUY"
            elif td and bar["high"] >= bar["ema8"] and bar["close"] < bar["ema8"]: sig = "SELL"
        elif strat == "MOMENTUM":
            if bar["mom"] > 0.0005 and tu: sig = "BUY"
            elif bar["mom"] < -0.0005 and td: sig = "SELL"

        if not sig: continue
        sl = round(bar["close"] - bar["atr"] * SL_M, 2) if sig == "BUY" else round(bar["close"] + bar["atr"] * SL_M, 2)
        tp = round(bar["close"] + bar["atr"] * TP_M, 2) if sig == "BUY" else round(bar["close"] - bar["atr"] * TP_M, 2)
        active = {"side": sig, "entry": bar["close"], "sl": sl, "tp": tp, "atr": bar["atr"]}

    wins = sum(1 for p in trades if p > 0)
    gp = sum(p for p in trades if p > 0)
    gl = abs(sum(p for p in trades if p < 0))
    pf = round(gp/gl, 2) if gl else 0
    net = round(sum(trades), 2)
    cp = 0; mdd = 0
    eq = 0
    for p in trades:
        eq += p
        if eq > cp: cp = eq
        dd = (cp - eq) / max(cp, 100) * 100
        if dd > mdd: mdd = dd
    return len(trades), round(len(trades)/days, 1), round(wins/len(trades)*100 if trades else 0), pf, net, round(mdd, 2)

pairs = [("XAUUSDm", "XAUUSD", 100), ("US30m", "US30", 10), ("JP225m", "JP225", 1), ("UK100m", "UK100", 1)]
results = []

for sym, label, mult in pairs:
    for strat in strategies:
        r = run_bt(sym, label, mult, strat)
        if r: results.append((label, strat, *r))

print(f"{'='*80}")
print(f"  HIGH FREQUENCY TEST — M5 (all strategies)")
print(f"{'='*80}")
print(f"  {'Pair':<8} {'Strategy':<12} {'Trades':>7} {'/hari':>6} {'WR%':>5} {'PF':>5} {'Net$':>9} {'DD%':>5}")
print(f"  {'-'*60}")
for r in results:
    print(f"  {r[0]:<8} {r[1]:<12} {r[2]:>7} {r[3]:>5.1f} {r[4]:>4.0f}% {r[5]:>5.2f} ${r[6]:>+7.2f} {r[7]:>4.1f}%")

mt5.shutdown()
