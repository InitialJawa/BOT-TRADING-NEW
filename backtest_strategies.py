"""
Backtest comparison: 6 different strategies on XAUUSD + US30
Same params: SL=0.3xATR, TP=0.6xATR, Trail=0.2xATR
Period: Oct 2025 - Jun 2026
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

LOT = 0.01
SL_M = 0.3
TP_M = 0.6
TRAIL_M = 0.2

STRATEGIES = ["EMA_CROSS", "PULLBACK", "DONCHIAN", "RSI_TREND", "MOMENTUM", "ATR_CH"]


def load_data(symbol):
    mt5.initialize()
    mt5.symbol_select(symbol, True)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5,
                                 datetime(2025, 10, 1), datetime(2026, 6, 10))
    mt5.shutdown()
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.columns = [c.lower() for c in df.columns]

    c = df["close"]; h = df["high"]; l = df["low"]
    df["ema8"] = c.ewm(span=8, adjust=False).mean()
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    df["ema34"] = c.ewm(span=34, adjust=False).mean()
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=14, adjust=False).mean()
    df["hh20"] = h.rolling(20).max()
    df["ll20"] = l.rolling(20).min()
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(span=7, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=7, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["mom"] = c.pct_change(3)
    df.dropna(inplace=True)
    return df


def run_backtest(df, strategy):
    trades = []
    active = None
    cons_loss = 0

    for idx in range(1, len(df)):
        bar = df.iloc[idx]
        prev = df.iloc[idx - 1]
        prev2 = df.iloc[idx - 2] if idx > 1 else prev

        if cons_loss >= 5:
            continue
        if bar["spread"] > 300:
            continue

        trend_up = bar["ema8"] > bar["ema34"]
        trend_dn = bar["ema8"] < bar["ema34"]

        # --- Manage active trade ---
        if active:
            if TRAIL_M > 0:
                actv = active["atr"] * TRAIL_M
                if active["side"] == "BUY":
                    pft = bar["close"] - active["entry"]
                    if pft > actv:
                        ns = bar["close"] - actv
                        if ns > active["sl"]: active["sl"] = ns
                else:
                    pft = active["entry"] - bar["close"]
                    if pft > actv:
                        ns = bar["close"] + actv
                        if ns < active["sl"]: active["sl"] = ns

            exit_p, exit_r = None, None
            if active["side"] == "BUY":
                if bar["high"] >= active["tp"]: exit_p, exit_r = active["tp"], "TP"
                elif bar["low"] <= active["sl"]: exit_p, exit_r = active["sl"], "SL"
            else:
                if bar["low"] <= active["tp"]: exit_p, exit_r = active["tp"], "TP"
                elif bar["high"] >= active["sl"]: exit_p, exit_r = active["sl"], "SL"

            if exit_p:
                if active["side"] == "BUY":
                    pnl = (exit_p - active["entry"]) * LOT * 100
                else:
                    pnl = (active["entry"] - exit_p) * LOT * 100
                trades.append({**active, "exit": exit_p, "reason": exit_r, "pnl": pnl})
                if pnl > 0: cons_loss = 0
                else: cons_loss += 1
                active = None
                continue
            else:
                continue

        # --- Signal detection ---
        signal = None

        if strategy == "EMA_CROSS":
            bull = prev["ema8"] <= prev["ema34"] and bar["ema8"] > bar["ema34"]
            bear = prev["ema8"] >= prev["ema34"] and bar["ema8"] < bar["ema34"]
            if bull: signal = ("BUY", "EMA_X")
            elif bear: signal = ("SELL", "EMA_X")

        elif strategy == "PULLBACK":
            body = abs(bar["close"] - bar["open"])
            if trend_up and bar["low"] <= bar["ema8"] and bar["close"] >= bar["ema8"] and body > 0:
                signal = ("BUY", "PULL")
            elif trend_dn and bar["high"] >= bar["ema8"] and bar["close"] <= bar["ema8"] and body > 0:
                signal = ("SELL", "PULL")

        elif strategy == "DONCHIAN":
            if bar["close"] > prev["hh20"]:
                signal = ("BUY", "DONC")
            elif bar["close"] < prev["ll20"]:
                signal = ("SELL", "DONC")

        elif strategy == "RSI_TREND":
            if trend_up and prev["rsi"] < 30 and bar["rsi"] < 30:
                signal = ("BUY", "RSI_")
            elif trend_dn and prev["rsi"] > 70 and bar["rsi"] > 70:
                signal = ("SELL", "RSI_")

        elif strategy == "MOMENTUM":
            if bar["mom"] > 0.001 and trend_up:
                signal = ("BUY", "MOM_")
            elif bar["mom"] < -0.001 and trend_dn:
                signal = ("SELL", "MOM_")

        elif strategy == "ATR_CH":
            if bar["close"] > bar["ema20"] + bar["atr"] * 0.5:
                signal = ("BUY", "ATCH")
            elif bar["close"] < bar["ema20"] - bar["atr"] * 0.5:
                signal = ("SELL", "ATCH")

        if not signal:
            continue

        side, reason = signal
        if side == "BUY":
            sl = round(bar["close"] - bar["atr"] * SL_M, 2)
            tp = round(bar["close"] + bar["atr"] * TP_M, 2)
        else:
            sl = round(bar["close"] + bar["atr"] * SL_M, 2)
            tp = round(bar["close"] - bar["atr"] * TP_M, 2)

        active = {"side": side, "reason": reason, "entry": bar["close"],
                  "sl": sl, "tp": tp, "atr": bar["atr"], "time": bar.name}

    pnls = [t["pnl"] for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    gp = sum(p for p in pnls if p > 0)
    gl = abs(sum(p for p in pnls if p < 0))
    peak = 10000.0; dd_max = 0.0; cur = 10000.0
    for t in trades:
        cur += t["pnl"]
        dd = (peak - cur) / peak * 100
        if dd > dd_max: dd_max = dd
        if cur > peak: peak = cur

    return {
        "trades": len(trades),
        "wr": wins / len(trades) * 100 if trades else 0,
        "pf": gp / gl if gl else 0,
        "net": sum(pnls),
        "dd": dd_max,
        "strategy": strategy,
    }


symbols = [
    ("XAUUSDm", "XAUUSD"),
    ("US30m",   "US30"),
]

results = {sym: {} for _, sym in symbols}

for mt5sym, label in symbols:
    df = load_data(mt5sym)
    print(f"\n{'='*55}")
    print(f"  {label} M5 — {len(df):,} bars")
    print(f"{'='*55}")
    print(f"  {'Strategy':<15} {'Trades':>6} {'WR%':>5} {'PF':>5} {'Net$':>8} {'DD%':>5}")
    print(f"  {'-'*45}")

    for strat in STRATEGIES:
        r = run_backtest(df, strat)
        results[label][strat] = r
        print(f"  {strat:<15} {r['trades']:>6} {r['wr']:>4.1f}% {r['pf']:>4.2f} ${r['net']:>+6.2f} {r['dd']:>4.2f}%")

# Combined ranking
print(f"\n\n{'='*55}")
print(f"  COMBINED RANKING (XAUUSD + US30)")
print(f"{'='*55}")
print(f"  {'Strategy':<15} {'Trades':>6} {'WR%':>5} {'PF':>5} {'Net$':>8} {'DD%':>5}")
print(f"  {'-'*45}")

ranks = []
for strat in STRATEGIES:
    total_trades = sum(results[s][strat]["trades"] for s in ["XAUUSD", "US30"])
    total_net = sum(results[s][strat]["net"] for s in ["XAUUSD", "US30"])
    avg_wr = sum(results[s][strat]["wr"] for s in ["XAUUSD", "US30"]) / 2
    avg_pf = sum(results[s][strat]["pf"] for s in ["XAUUSD", "US30"]) / 2
    avg_dd = sum(results[s][strat]["dd"] for s in ["XAUUSD", "US30"]) / 2
    ranks.append((strat, total_trades, avg_wr, avg_pf, total_net, avg_dd))

ranks.sort(key=lambda x: x[4], reverse=True)  # sort by net profit desc

for s, t, w, p, n, d in ranks:
    print(f"  {s:<15} {t:>6} {w:>4.1f}% {p:>4.2f} ${n:>+6.2f} {d:>4.2f}%")
