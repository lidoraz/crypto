from Data.Crypto.symbols import exchange_symbol_pairs
import pandas as pd
import ccxt


def get_coins(only_exchange=None):
    if only_exchange:
        print(f'Filtered coins only traded in: {only_exchange}')
        coins = [p[1].split('/')[0] for p in exchange_symbol_pairs if p[0] == only_exchange.lower()]
    else:
        coins = [p[1].split('/')[0] for p in exchange_symbol_pairs]
    if not len(coins):
        raise ValueError('No coins were selected to follow')
    return coins


def _resample_from_ohlcv(ohlcv, coin, interval):
    if 'curr_ts_db' not in ohlcv.attrs:
        raise ValueError('ohlcv must have attrs = curr_ts_db')
    if interval.lower() not in ['1min', '1t']:
        ohlcv_up = pd.concat([
            ohlcv['open'].resample(interval).first(),
            ohlcv['high'].resample(interval).max(),
            ohlcv['low'].resample(interval).min(),
            ohlcv['close'].resample(interval).last(),
            ohlcv['volume'].resample(interval).sum()], axis=1)
        ohlcv_up.attrs['curr_ts_db'] = ohlcv.attrs['curr_ts_db']
        ohlcv = ohlcv_up
    ohlcv.attrs['interval'] = interval
    ohlcv.attrs['symbol'] = coin
    return ohlcv.sort_index()


def get_latest_ts_db(db, coin):
    exchange_name, symbol = get_exchange_symbol_by_coin(coin)
    db_symbol = f'{exchange_name}_{symbol}'.upper()
    return db.get_latest_ts(db_symbol, '1m')


def get_candles_from_db(db, coin, tf, start_ts=None, start_date=None, localize='Israel'):
    if start_date and start_ts:
        raise ValueError('Only one start can be set.')
    if start_ts and not isinstance(start_ts, int):
        raise ValueError('start_ts not valid')
    if start_date and not isinstance(start_date, str):
        raise ValueError('start_date not valid')
    exchange_name, symbol = get_exchange_symbol_by_coin(coin)
    # TODO: BASE COIN NEED TO BE SOME KIND ELSE not HARD CODED HERE. Maybe take from exchange_symbol_pairs
    symbol_str = f'{coin}/USDT'
    df = _get_candles_from_db(db, exchange_name, symbol_str, tf, start_ts=start_ts, start_date=start_date, localize=localize)
    return df


def _get_candles_from_db(db, exchange_name, symbol, tf, start_ts=None, start_date=None, localize=None):
    db_symbol = f'{exchange_name}_{symbol}'.upper()
    df = db.get_df(db_symbol, '1m', start_ts, start_date)
    if df is None:
        print(f'Warning: {exchange_name}_{db_symbol} does not exists!')
        return None
    df = _resample_from_ohlcv(df, symbol, tf)
    if localize:
        df = df.tz_convert(localize)
    return df


def get_exchange_symbol_by_coin(coin):
    exchange_name, symbol = [(ex, sy) for ex, sy in exchange_symbol_pairs if sy.startswith(coin)][0]
    return exchange_name, symbol


# not used as persistence is being used, but can be
def get_candles_from_ccxt(coin, tf):
    exchange_name, symbol = get_exchange_symbol_by_coin(coin)
    exchange = getattr(ccxt, exchange_name)({
        'enableRateLimit': True,  # required by the Manual
    })
    df = exchange.fetch_ohlcv(symbol, tf.lower())
    df = pd.DataFrame(df, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
    df = df.set_index('ts')
    df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_convert('Israel')
    df.attrs['interval'] = tf
    df.attrs['symbol'] = coin
    return df
