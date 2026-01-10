import MetaTrader5 as mt
import config
import pandas as pd

def debug_symbol(symbol):
    if not mt.initialize():
        print("initialize() failed")
        return

    if not mt.login(config.MT5_LOGIN, password=config.MT5_PASS, server=config.MT5_SERVER):
        print("login failed")
        mt.shutdown()
        return

    print(f"Checking {symbol}...")
    # Check how many bars are available
    count = mt.positions_total() # Not bars
    
    # Try to get 1 bar at 0
    rates = mt.copy_rates_from_pos(symbol, config.TIMEFRAME, 0, 1)
    if rates is None:
        print(f"Error getting 1 bar: {mt.last_error()}")
    else:
        print("Successfully got 1 bar")

    # Try to get many bars
    requested = 2000000
    rates = mt.copy_rates_from_pos(symbol, config.TIMEFRAME, 0, requested)
    if rates is None:
        err = mt.last_error()
        print(f"Error getting {requested} bars: {err}")
        if err[0] == mt.RES_E_NOT_FOUND:
            print("Likely not enough bars available in terminal history.")
        # Try to find max available
        # Binary search or just check in chunks
        print("Checking max available bars...")
        for bars in [1000000, 500000, 200000, 100000, 50000]:
            r = mt.copy_rates_from_pos(symbol, config.TIMEFRAME, 0, bars)
            if r is not None:
                print(f"Max available (roughly): {len(r)} (requested {bars})")
                break
    else:
        print(f"Successfully got {len(rates)} bars")

    # TEST: Try to get data from 1 year ago using copy_rates_from
    from datetime import datetime
    import datetime as dt
    utc_from = datetime.now() - dt.timedelta(days=365)
    print(f"Testing copy_rates_from starting from {utc_from}...")
    rates = mt.copy_rates_from(symbol, config.TIMEFRAME, utc_from, 100)
    if rates is None:
        print(f"Error getting historical bars by date: {mt.last_error()}")
    else:
        print(f"Successfully got {len(rates)} historical bars by date")

    mt.shutdown()

if __name__ == "__main__":
    debug_symbol("XAGUSD")
    debug_symbol("XAUUSD")
