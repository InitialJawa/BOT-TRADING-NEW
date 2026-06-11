import MetaTrader5 as mt5
mt5.initialize()
acc = mt5.account_info()
print(f"Balance={acc.balance} Equity={acc.equity} Currency={acc.currency} Leverage=1:{acc.leverage}")

for sym_name in ["XAUUSDm", "JP225m", "US30m"]:
    sym = mt5.symbol_info(sym_name)
    if sym:
        print(f"\n{sym_name}:")
        print(f"  trade_mode={sym.trade_mode}")
        print(f"  volume_min={sym.volume_min} volume_max={sym.volume_max} volume_step={sym.volume_step}")
        print(f"  margin_initial={sym.margin_initial} margin_maintenance={sym.margin_maintenance}")
        print(f"  contract_size={sym.trade_contract_size}")
        print(f"  price={sym.bid}/{sym.ask}")

    # Calc margin for current lot
    for lot in [0.01, 1.0]:
        margin = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, sym_name, lot, sym.ask if sym else 0)
        if margin:
            print(f"  margin_{lot}lot={margin} ({margin/acc.equity*100:.1f}% equity)")

mt5.shutdown()
