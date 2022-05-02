import ccxt
import pandas as pd
from Nasdaq.Persistence import Persistence

# exchanges = [ccxt.binance(), ccxt.kucoin(), ccxt.mexc(), ccxt.bybit(), ccxt.coinex(), ]
# print('created exchanges')
#
# def get_data(symbol, resample):
#     symbol = symbol + '/USDT'
#
#     timeframe = resample.lower().replace('min', 'm')
#     # exchange = ccxt.binance()
#     for exchange in exchanges:
#         try:
#             ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
#             # print datetime and other values
#             # for x in ohlcv:
#             #     print(exchange.iso8601(x[0]), x)
#             cols = ['ts', 'open', 'high', 'low', 'close', 'volume']
#             df_ohlcv = pd.DataFrame(ohlcv, columns=cols)
#             df_ohlcv['ts'] = pd.to_datetime(df_ohlcv['ts'].apply(exchange.iso8601))
#             df_ohlcv = df_ohlcv.set_index('ts')
#             df_ohlcv.attrs['interval'] = resample
#             print(exchange.name, 'fetched with', symbol, timeframe)
#             return df_ohlcv, exchange.name
#         except:
#             print(exchange.name, ' failed.. Trying different exchange')
#     raise

# TODO: FIX KUCOIN IT IS CRAP
exchance_symbol_pairs = [
    ('binance', 'ACA/USDT'),
    ('binance', 'ETH/USDT'),
    ('binance', 'SAND/USDT'),
    ('binance', 'DOT/USDT'),
    ('binance', 'SOL/USDT'),
    ('binance', 'ADA/USDT'),
    ('binance', 'AXS/USDT'),
    ('binance', 'BTC/USDT'),
    ('binance', 'KSM/USDT'),
    ('binance', 'XRP/USDT'),
    ('binance', 'MANA/USDT'),
    ('binance', 'XLM/USDT'),
    ('binance', 'EGLD/USDT'),
    ('binance', 'FLUX/USDT'),
    ('binance', 'CRV/USDT'),
    ('binance', 'APE/USDT'),
    ('binance', 'ROSE/USDT'),
    ('binance', 'LUNA/USDT'),
    ('binance', 'OGN/USDT'),
    ('binance', 'RNDR/USDT'),
    ('binance', 'GLMR/USDT'),
    ('binance', 'BNB/USDT'),
    ('binance', 'SHIB/USDT'),
    ('binance', 'CAKE/USDT'),
    ('binance', 'FTM/USDT'),
    ('binance', 'RUNE/USDT'),
    ('binance', 'KDA/USDT'),
    ('binance', 'MATIC/USDT'),
    ('binance', 'MOVR/USDT'),
    ('binance', 'GALA/USDT'),
    ('kucoin', 'QRDO/USDT'),
    ('kucoin', 'HTR/USDT'),
    ('kucoin', 'RMRK/USDT'),
    ('kucoin', 'SOUL/USDT'),
    ('kucoin', 'LYXE/USDT'),
    ('kucoin', 'TEL/USDT'),
    ('kucoin', 'VRA/USDT'),
    # ('mexc','GCOIN/USDT')
]


def get_coins():
    coins = [p[1].split('/')[0] for p in exchance_symbol_pairs]
    return coins


def _resample_from_ohlcv(ohlcv, interval):
    if interval != '1Min':
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
