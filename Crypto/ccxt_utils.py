import pandas as pd

from Crypto.symbols import exchance_symbol_pairs



def get_coins():
    coins = [p[1].split('/')[0] for p in exchance_symbol_pairs]
    return coins


def _resample_from_ohlcv(ohlcv, interval):
    if interval.lower() not in ['1min', '1t']:
        ohlcv = pd.concat([
            ohlcv['open'].resample(interval).first(),
            ohlcv['high'].resample(interval).max(),
            ohlcv['low'].resample(interval).min(),
            ohlcv['close'].resample(interval).last(),
            ohlcv['volume'].resample(interval).sum()], axis=1)
    ohlcv.attrs['interval'] = interval
    return ohlcv.sort_index()


# add limit time- time_before\
# TODO; this lass really needs an option to get data from regular datetime, timestamp is very annoying
def get_candles_from_db(db, coin, tf, start_ts=None, start_date=None):
    if start_date and start_ts:
        raise ValueError('Only one start can be set.')
    exchange_name, symbol = \
    [(exchange_name, symbol) for exchange_name, symbol in exchance_symbol_pairs if symbol.startswith(coin)][0]
    symbol_str = f'{coin}/USDT'
    return _get_candles_from_db(db, exchange_name, symbol_str, tf, start_ts=start_ts, start_date=start_date)


def _get_candles_from_db(db, exchange_name, symbol, tf, start_ts=None, start_date=None):
    db_symbol = f'{exchange_name}_{symbol}'.upper()
    df = db.get_df(db_symbol, '1m', start_ts, start_date)
    try:
        df_ohlcv = _resample_from_ohlcv(df, tf)
        return df_ohlcv
    except Exception as e:
        print(db_symbol, type(e).__name__, str(e))
        raise
