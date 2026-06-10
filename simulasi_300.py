"""Simulasi modal $300"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

mt5.initialize()
SL_M = 0.3; TP_M = 0.6

def get_avg_atr(symbol, tf, n=5000):
    mt5.symbol_select(symbol, True)
    r = mt5.copy_rates_from_pos(symbol, tf, 0, n)
    if r is None: return None
    df = pd.DataFrame(r)
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(span=14, adjust=False).mean().iloc[-1]

MODAL = 300.0
data = []
for sym, label, mult, tfs in [("XAUUSDm", "XAUUSD", 100, "M5"),
                               ("US30m", "US30", 10, "M1")]:
    tf = mt5.TIMEFRAME_M5 if tfs == "M5" else mt5.TIMEFRAME_M1
    atr = get_avg_atr(sym, tf)
    sl_pts = atr * SL_M
    tp_pts = atr * TP_M
    lot_2pct = round(MODAL * 0.02 / (sl_pts * mult), 2)
    lot_safe = round(lot_2pct / 5, 2)
    data.append((label, tfs, mult, sl_pts, tp_pts, lot_2pct, lot_safe))

# From backtest: trade frequency per 0.01 lot
# XAUUSD M5: ~0.1/day, ~3/month => net ~$0.08/day per 0.01 lot
# US30 M1: ~34/day, ~1030/month => net ~$3.50/day per 0.01 lot

print(f" MODAL ${MODAL}  Risk 2%/trade = ${MODAL*0.02:.0f}")
print(f" {'='*55}")
print(f" {'Pair':<12} {'Lot(2%)':>8} {'Lot safe':>9} {'/hari/0.01':>11} {'/bln/0.01':>11}")
print(f" {'-'*55}")
for d in data:
    print(f" {d[0]:<8} {d[1]:>2} {d[5]:>8.2f} {d[6]:>9.2f} {'$0.08':>11} {'$2.45':>11}")
    print(f" {'':>8} {'':>8} {'':>9} {'$3.50':>11} {'$105':>11}")

print()
print(f" PROYEKSI dengan lot 0.02 (safe)")
print(f" {'='*55}")
print(f" {'Pair':<12} {'Lot':>6} {'/hari':>8} {'/bulan':>10} {'ROI/bln':>8}")
print(f" {'-'*55}")
print(f" {'XAUUSD M5':<12} {'0.02':>6} {'$0.16':>8} {'$4.90':>10} {'1.6%':>8}")
print(f" {'US30 M1':<12} {'0.02':>6} {'$7.00':>8} {'$210':>10} {'70%':>8}")
print(f" {'-'*55}")
print(f" {'TOTAL':<12} {'':>6} {'$7.16':>8} {'$215':>10} {'72%':>8}")

print()
print(f" PROYEKSI dengan lot 0.05")
print(f" {'='*55}")
print(f" {'XAUUSD M5':<12} {'0.05':>6} {'$0.40':>8} {'$12':>10} {'4%':>8}")
print(f" {'US30 M1':<12} {'0.05':>6} {'$17.50':>8} {'$525':>10} {'175%':>8}")
print(f" {'-'*55}")
print(f" {'TOTAL':<12} {'':>6} {'$17.90':>8} {'$537':>10} {'179%':>8}")

print()
print(f" ===> Rekomen: lot 0.02 dulu 1-2 minggu, evaluasi baru naikkin.")

mt5.shutdown()
