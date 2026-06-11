# BOT MANAGER — Master Control Document

> **Panggil file ini** setiap AI baru masuk. Semua informasi project ada di sini.
>
> **Update 11-Jun-2026:** Semua management/audit/research files dipindah dari root ke `BOT_MANAGER/`.
> - compound_manager.py, auto_tuner.py, check_margin.py → `BOT_MANAGER/`
> - Audit/, backtest_results/, backtest_scalping/ → `BOT_MANAGER/`
> - logs/ (compound.log, auto_tuner.log) → `BOT_MANAGER/logs/`
> - Root hanya berisi: `bot_fabio/`, `Bot_archive/`, `.git/`, `.gitignore`

---

## 1. PROJECT OVERVIEW

| Item | Value |
|------|-------|
| **Goal** | Maximize profit via scalping strategies with auto-compounding |
| **Broker** | Exness-MT5Trial6 (demo) |
| **Login** | 413889745 |
| **Balance awal** | 5.000.000 IDR (~$278 USD) |
| **Balance skrg** | 5.194.446 IDR |
| **Leverage** | 1:2000 |
| **Timeframe** | M5 |
| **USDIDR rate** | ~17.960 |
| **Telegram** | DISABLED (no .env) |
| **Python** | C:\Python314\python.exe |

---

## 2. AKTIF BOT

### bot_fabio (Fabio) — ✅ RUNNING
| Pair | Lot | Strategy | Magic | Status |
|------|-----|----------|-------|--------|
| XAUUSDm | 0.01 | TREND_RE | 25062026 | ✅ Active |
| US30m | 0.0 | TREND_RE | 25062027 | ⏸️ skip (eq < $3000) |
| JP225m | 0.0 | TREND_RE | 25062028 | ⏸️ DISABLED (PF 0.64, rugi) |

**Mode:** instant | **SL/TP:** 0.3/0.6 ATR | **Poll:** 5s

### bot_hendro — ❌ STOPPED (all lots 0.0)

### Archived bots (Bot_archive/):
- `bot_original/` — EMA_CROSS, dead
- `bot_live/` — Predecessor Fabio, stopped
- `bot_hendro/` — ADAPTIVE regime-switching, archived

---

## 3. COMPOUND MANAGER

**File:** `BOT_MANAGER\compound_manager.py`
**Schedule:** Task Scheduler `\CompoundManager` — tiap 1 jam
**Python:** `C:\Python314\python.exe -X utf8 BOT_MANAGER\compound_manager.py`

### AUTO-TUNER (safety net)
**File:** `BOT_MANAGER\auto_tuner.py`
**Schedule:** Task Scheduler `\AutoTunerBot` — tiap 30 menit
**Function:** Monitor PnL/WR per strategy, auto-switch if WR < 20% or PnL < -$200

### Pair Config (live):

| Pair | Ratio | min_eq_usd | min_lot | lot_step | Rumus |
|------|-------|-----------|---------|---------|-------|
| XAUUSDm | 30000 | $0 | 0.01 | 0.01 | eq / 30000 |
| JP225m | 500 | **$99999** | 1.0 | 1.0 | eq / 500 → DISABLED (PF 0.64) |
| US30m | 30000 | $3000 | 0.01 | 0.01 | eq / 30000 |

### Cara kerja:
1. Baca equity USD (auto-convert IDR → USD via USDIDRm rate)
2. Hitung ulang lot per pair: `lot = round(equity / ratio / lot_step) * lot_step`
3. Jika equity < min_eq_usd → lot = 0 (skip)
4. Jika ada perubahan → update config.yaml → kill bot → restart bot

### Margin check (1:2000):
| Pair | 1 lot margin (% equity) |
|------|------------------------|
| XAUUSDm 0.01 | 36.6K IDR (0.7%) |
| JP225m 1.0 | 36.0K IDR (0.7%) |
| US30m 0.01 | 22.6K IDR (0.4%) |

---

## 4. ALL STRATEGIES

| Strategy | Logic | WR (backtest) | PF |
|----------|-------|---------------|-----|
| **TREND_RE** | Entry tiap bar sesuai arah trend (EMA 8 > 34 = buy, else sell). Re-entry after SL allowed. | 46-47% | 1.35-1.40 |
| **MOMENTUM** | Trend + momentum threshold (close change > 0.05% over 3 bars) | ~50% | 1.41-1.47 |
| **EMA_CROSS** | Classic EMA 8/34 crossover | ~40% | 1.50 |
| **PULLBACK** | Trend + harga sentuh EMA fast lawan arah | ~45% | 1.38 |

**Strategy params (shared):**
```yaml
ema_fast: 8
ema_slow: 34
atr_period: 14
sl_atr_mult: 0.3
tp_atr_mult: 0.6
trailing_activation: 0.2
momentum_threshold: 0.0005
```

---

## 5. RISK PARAMETERS

```yaml
max_daily_loss_pct: 5.0
max_consecutive_losses: 5
max_positions: 3
circuit_breaker_dd_pct: 15.0
```

---

## 6. KEY DECISIONS (dont change without discussion)

| Decision | Alasan |
|----------|--------|
| TREND_RE untuk semua pair | Backtest profit tertinggi |
| Auto-tuner safety net only | Semua skema auto-tuner tidak improve vs static |
| Regime switching discarded | ADX/vol/direction switching rugi $16K vs static |
| Compound pair-specific ratio | XAU=eq/30000, JP225=eq/500 (bukan satu ratio) |
| US30 multiplier 1 (bukan 100) | Semua backtest sebelumnya overestimate 100x |
| JP225 profit dalam JPY | Perlu konversi USDJPY (~160) |
| Session filter disabled | Rugi 40% profit saat diaktifkan |
| US30 skip until $3K | DD overshoot jika equity kecil |
| JP225 DISABLED | TREND_RE JP225 PF 0.64 — rugi di backtest & live |

---

## 7. FILE STRUCTURE

```
├── BOT_MANAGER/                    ← SEMUA management/audit/research ada di sini
│   ├── BOT_MANAGER.md              ← THIS FILE (master control)
│   ├── DIARY.md                    ← Manager diary (catat SEMUA perubahan)
│   ├── update_status.py            # Auto-refresh CURRENT STATUS di BOT_MANAGER.md
│   ├── compound_manager.py         # Auto-adjust lot based on equity
│   ├── compound_state.json         # Compound manager state
│   ├── auto_tuner.py               # Strategy rotation monitor
│   ├── auto_tuner_state.json       # Auto-tuner state
│   ├── check_margin.py             # Margin check utility
│   ├── BOT_COMPARISON.md           # Bot performance comparison
│   ├── SUMMARY.md                  # Old project summary
│   ├── bot_err.txt                 # Bot stderr capture
│   ├── bot_out.txt                 # Bot stdout capture
│   ├── Audit/                      # Backtest scripts (22 files)
│   ├── backtest_results/           # Backtest JSON results
│   ├── backtest_scalping/          # Optimized backtest engine
│   └── logs/
│       ├── compound.log            # Compound manager history
│       └── auto_tuner.log          # Auto-tuner history
├── bot_fabio/                      # Active bot (tidak dipindah)
│   ├── bot.py                      # Main engine
│   ├── config.yaml                 # Live config (diupdate compound manager)
│   ├── strategy.py                 # Strategy engine (4 strategies)
│   ├── telegram.py                 # Telegram notifier (DISABLED)
│   ├── check_status.py             # Quick status check
│   ├── check_us30.py               # US30 performance check
│   ├── test_mt5.py                 # MT5 connectivity test
│   ├── export_trades.py            # Export trade history
│   ├── state_XAUUSDm.json          # Bot state (consecutive losses, daily PnL)
│   ├── state_JP225m.json           # Bot state
│   ├── logs/bot_YYYYMMDD.log       # Daily trading log
│   └── run.bat                     # Windows double-click launcher
├── Bot_archive/                    # bot_original, bot_live, bot_hendro
└── .git/
```

---

## 8. COMMON COMMANDS

| Command | Description |
|---------|-------------|
| `cd BOT_MANAGER && python update_status.py` | Refresh CURRENT STATUS di BOT_MANAGER.md |
| `cd BOT_MANAGER && python compound_manager.py` | Run lot adjustment (manual) |
| `cd BOT_MANAGER && python auto_tuner.py` | Run strategy monitor |
| `cd BOT_MANAGER && python check_margin.py` | Check margin requirements |
| `cd bot_fabio && python check_status.py` | Check account balance, positions, state |
| `cd bot_fabio && python bot.py` | Start bot manually |
| `cd bot_fabio && Get-Content logs\bot_20260611.log -Tail 20` | Check latest trades |
| `type BOT_MANAGER\logs\compound.log` | Check compound manager history |
| `type BOT_MANAGER\logs\auto_tuner.log` | Check auto-tuner history |

---

## 9. ERRORS & TROUBLESHOOTING

| Error | Cause | Fix |
|-------|-------|-----|
| 10016 (not enough money) | Insufficient margin/free margin | Reduce lot or wait for equity to grow |
| 10027 (auto trading disabled) | Server rejected trade | Restart bot / reconnect MT5 |
| 10014 (invalid order) | Bad SL/TP or volume | Check config min_lot/lot_step |
| division by zero | MT5 returning balance=0 (transient) | Bot auto-recovers on next cycle |
| type_str not found | MT5 API version mismatch | Use `p.type` instead |

---

## 10. CURRENT STATUS (real-time) — auto-updated tiap 15 menit

<!-- STATUS_START -->
*Auto-updated: 2026-06-11 20:00:57*  
```
Balance: $4997705.73 | Equity: $5000860.24 | Profit: $3154.51
XAUUSDm      OPEN SELL Vol=0.01 Entry=4080.44 SL=4084.85 TP=4076.26 Price=4080.60 Profit=-2883.60
US30m        NO POSITION
JP225m       OPEN SELL Vol=1.00 Entry=64397.40 SL=64380.90 TP=64326.80 Price=64343.80 Profit=6038.11
```
<!-- STATUS_END -->

---

## 11. AI AGENT ONBOARDING CHECKLIST

Ketika AI baru masuk dan disuruh "panggil BOT MANAGER":
1. ✅ Baca file ini (`BOT_MANAGER.md`) + diary (`DIARY.md`)
2. ✅ Cek status real-time: `python update_status.py` (atau `cd ../bot_fabio && python check_status.py`)
3. ✅ Cek log terbaru: `Get-Content bot_fabio/logs/bot_20260611.log -Tail 20`
4. ✅ Cek compound state: `BOT_MANAGER\compound_state.json`
5. ✅ Cek running process: `Get-Process python`
6. ✅ Cek jadwal: `schtasks /query /fo LIST /v | Select-String "BotStatus|CompoundManager|AutoTuner"`

**WAJIB:** Setiap kali ada perubahan (ganti config, restart bot, ubah ratio, dll):
- ✏️ Tulis di `BOT_MANAGER/DIARY.md` — format: `### HH:MM — Judul` + deskripsi singkat
- 🔄 Jalankan `python update_status.py` untuk refresh status di BOT_MANAGER.md
