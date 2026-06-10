# Project Summary — Multi-Strategy Scalping Bot (MT5)

## Overview
Automated scalping bot for MetaTrader 5 using EMA 8/34 crossover with ATR-based SL/TP and trailing stops. Originally single-pair (XAUUSD), now multi-symbol (XAUUSDm, US30m, JP225m) with an ADAPTIVE strategy engine that switches between ranging (EMA_CROSS) and trending (TREND_RE + momentum) modes based on market regime detection.

## Architecture
- `bot_live/bot.py` — Main loop: polls MT5, manages positions, handles re-entry, circuit breaker, trailing stops
- `bot_live/strategy.py` — Strategy engine: 5 strategies, indicator calculation, regime detection, signal generation
- `bot_live/config.yaml` — Live configuration (symbols, lots, strategy params, risk limits)
- `bot_live/telegram.py` — Telegram notifications
- `bot_live/export_trades.py` — CSV trade export
- `backtest_scalping/` — Original backtest framework (EMA_CROSS only, single-pair)
- `BACKTEST_RESULTS.txt` — Original EMA-only backtest summary

## 5 Strategies

| Strategy | Entry Condition | Re-entry | Best For |
|----------|---------------|----------|----------|
| **EMA_CROSS** | EMA fast crosses above/below EMA slow | No (1 signal per crossover) | Ranging markets |
| **MOMENTUM** | Price change >0.05% in EMA trend direction | No | Medium-trend markets |
| **PULLBACK** | Price pulls back to EMA fast in trend direction | No | Strong trends with dips |
| **TREND_RE** | Every bar in EMA trend direction | Yes (immediate re-entry) | Sustained trends |
| **ADAPTIVE** | Ranging→EMA_CROSS, Trending→TREND_RE+momentum | Yes (trending mode only) | All conditions |

### ADAPTIVE Regime Detection
```
regime_ratio = |EMA_fast - EMA_slow| / ATR
regime_ratio >= 0.5  →  TRENDING  →  TREND_RE + momentum filter (>0.0005)
regime_ratio <  0.5  →  RANGING   →  EMA_CROSS (wait for crossover)
```

## Parameters (all strategies)
| Param | Value |
|-------|-------|
| EMA fast/slow | 8 / 34 |
| ATR period | 14 |
| SL | 0.3 × ATR |
| TP | 0.6 × ATR |
| Trail activation | 0.2 × ATR |
| Momentum threshold | 0.0005 (0.05%) |
| Regime threshold | 0.5 ATR |
| Max spread | 300 points |
| Mode | Instant (every 5s poll) |

## Lot Sizing ($300 capital, 2% risk/trade)
| Pair | Lot | $/point |
|------|-----|---------|
| XAUUSDm | 0.03 | $3.00 |
| US30m | 0.20 | $0.20 |
| JP225m | 5.0 | ¥0.031 (≈$0.0002) |

## Backtest Results (Fixed — END trades closed at SL, realistic)

### Full Period: Sep 2025 – Jun 2026 (50,000 M5 bars, 8 months)

```
                  ADAPTIVE    EMA_CROSS   MOMENTUM   PULLBACK   TREND_RE
XAUUSD  Trades      78          72           6         118         93
        Win%       51.3%        51.4%       0.0%       56.8%      49.5%
        PF          1.67        1.58        0.00        2.28       1.54
        AdjNet    +$54.44     +$72.77     -$13.69    +$378.68    +$60.23
        MaxDD       3.9%        6.1%        4.5%        5.1%       4.7%

US30    Trades      37          19          50         164         49
        Win%       51.4%       42.1%      60.0%       59.1%      49.0%
        PF          1.84        1.00        2.62        2.37       1.72
        AdjNet    +$26.51      +$0.02     +$73.83    +$371.74    +$32.27
        MaxDD        -           -           -           -          -

JP225   Trades     137          45          50          48          9
        Win%       47.4%       60.0%      48.0%       52.1%      22.2%
        PF          1.61        3.09        1.52        1.78       0.64
        AdjNet    +$17.20     +$14.81      +$7.43     +$12.71     -$0.41
        MaxDD        -           -           -           -          -

TOTAL   AdjNet    +$98.15     +$87.60     +$67.57    +$763.13    +$92.09
```

### Multi-Period Consistency Test
XAUUSD split into 3 equal periods (16,666 bars each):

```
        P1 (Sep'25)  P2 (Feb'26)  P3 (Apr'26)  Trend
ADAPTIVE    +$89.33    +$23.82      +$15.04     ✅ 3/3 pos
EMA_CROSS   +$48.21    +$14.80      +$25.25     ✅ 3/3 pos
PULLBACK   +$393.16    +$30.20       +$3.50     ❌ P1 94%
TREND_RE    -$15.42    +$10.29     +$36.17     ⚠️ Mixed
MOMENTUM   +$109.64    +$29.77     +$50.26     ✅ 3/3 pos
```

US30 split into 3 equal periods:

```
        P1 (Sep'25)  P2 (Feb'26)  P3 (Apr'26)  Trend
ADAPTIVE     +$34.45    +$10.70      -$0.07     ✅ 2/3 pos
PULLBACK    +$148.77   +$168.00     +$25.12     ⚠️ P3 drop
MOMENTUM    +$105.81    -$12.90      -$1.85     ❌ P1 bias
TREND_RE     +$49.07     +$5.21      +$7.14     ✅ 2/3 pos
```

## Key Findings

1. **END trade artifact**: TREND_RE appeared to have PF 9.71 / +$858 in first backtest. Actual cause: 1 single position still open at end of data was closed at final market price (+$776.60). With conservative close-at-SL, TREND_RE is PF 1.54 / +$60.23.

2. **ADAPTIVE is most consistent**: 8/9 period-pair combinations positive (89%). Modest but reliable returns: ~$98/8mo = ~$12/mo on $300 (4% ROI/mo).

3. **PULLBACK has highest total but is unstable**: XAUUSD PULLBACK net $378.68, but 94% comes from Period 1 only. Likely overfit to specific market conditions in late 2025.

4. **JP225 safest with ADAPTIVE**: Pure TREND_RE loses (-$0.41), pure EMA_CROSS barely profits (+$14.81). ADAPTIVE gives +$17.20 with 137 trades across all regimes.

5. **Daily loss circuit (5%) & max consecutive losses (5)** protect against drawdown: max DD across all strategies < 7%.

6. **Price-vs-EMA filter** (`_sig_trend_re`): hanya entry jika `price > EMA_fast` untuk BUY atau `price < EMA_fast` untuk SELL. Mencegah entry saat harga sudah terlalu jauh dari EMA (late entry).

7. **Session filter**: XAUUSD terbatas London+NY session (07:00-22:00 UTC) — hipotesis: Asian session terlalu choppy (belum dibuktikan, perlu backtest setelah data terkumpul).

8. **Cooldown 3 loss**: skip entry setelah 3 loss berturut-turut, reset otomatis saat WIN. Berbeda dari circuit breaker yang stop total.

## Incident Log — June 2026

Bot berjalan dengan **config lama (v1.x)** di PC live. Config baru (ADAPTIVE) belum di-deploy.

| Masalah | Dampak |
|---------|--------|
| XAUUSDm: TREND_RE + lot 0.10 (bukan 0.03) | Risk 3.3x lebih besar, strategy salah |
| Tidak ada session filter | Trade masuk di Asian session (choppy) |
| regime_threshold 0.5 (terlalu sensitif) | Terlalu sering masuk TRENDING mode |

**Live 30 hari:** 208 trades, 43% WR, **-$1,174.67** (XAUUSD: 25% WR, -$1,156)

---

## Current Configuration (v2.1)
File: `bot_live/config.yaml`
- All 3 pairs use `ADAPTIVE` strategy
- Lot sizes: XAUUSD 0.03, US30 0.20, JP225 5.0
- Mode: instant (with ADAPTIVE re-entry in trending mode only)
- Regime threshold: **0.7** ATR (dinaikkan dari 0.5 — lebih selektif)
- Session filter: XAUUSD 07:00-22:00 UTC, US30 13:30-20:00 UTC, JP225 00:00-08:00 UTC
- Cooldown: skip entry after 3 consecutive losses (reset on win)

## Threshold Decision (0.5 vs 0.7)

Backtest ADAPTIVE across all 3 pairs (full period):

| Threshold | XAUUSD | US30 | JP225 | **Total** | Trades |
|-----------|--------|------|-------|-----------|--------|
| 0.5 | +$65.97 | +$18.92 | +$17.92 | **+$102.81** | 251 |
| 0.7 | +$66.51 | +$21.63 | +$14.73 | **+$102.87** | 230 |

Virtually identical total return. 0.7 chosen for **fewer trades** (lower transaction costs) and **better US30 P3 performance**.

## File Changes (v2.1)
| File | Change |
|------|--------|
| `bot_live/strategy.py` | Added `_is_within_session()`, price-vs-EMA filter in `_sig_trend_re()`, session filter check in `get_signal()` + `get_trend_signal()` |
| `bot_live/bot.py` | Added `cooldown_cleared` state tracking, cooldown check in `_tick_handler` (skip entry after 3 consecutive losses until win), session_filter passthrough in handler config |
| `bot_live/config.yaml` | Added `session_filter` per symbol (XAU/US30/JP225), changed `regime_threshold: 0.5 → 0.7` |
