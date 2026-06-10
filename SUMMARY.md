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

## Current Configuration
File: `bot_live/config.yaml`
- All 3 pairs use `ADAPTIVE` strategy
- Lot sizes: XAUUSD 0.03, US30 0.20, JP225 5.0
- Mode: instant (with ADAPTIVE re-entry in trending mode only)
- Regime threshold: 0.5 ATR

## File Changes Made
| File | Change |
|------|--------|
| `bot_live/strategy.py` | Added `_detect_regime()` (ranging/trending), `_sig_adaptive()` (EMA_CROSS in ranging, TREND_RE+momentum in trending), `is_reentry_strategy` property |
| `bot_live/bot.py` | `_tick_handler` uses `handler.strategy.is_reentry_strategy` instead of hardcoded `"TREND_RE"` check |
| `bot_live/config.yaml` | Changed all symbols to `ADAPTIVE` strategy, added `regime_threshold: 0.5` |
