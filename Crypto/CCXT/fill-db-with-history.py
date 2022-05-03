# # -*- coding: utf-8 -*-
# import os
# import sys
# # -----------------------------------------------------------------------------
# from Crypto.DataProcessing.data_consts import COINS
# from Nasdaq.Persistence import Persistence
#
# # -----------------------------------------------------------------------------
#
# import ccxt  # noqa: E402
#
# print('CCXT Version:', ccxt.__version__)
#
# # -----------------------------------------------------------------------------
#
# from datetime import datetime
# import random
#
#
# def fetch_ohlcv(db, exchange, symbol, timeframe, limit):
#     since = None
#     ts = None
#     random_sec_to_wait = 6
#     while True:
#         try:
#             ts = datetime.utcnow()
#             time_to_sleep = 60 - ts.second + random.randint(0,
#                                                             random_sec_to_wait)  # randomize acc time to reduce chance for ddos protection
#             use_ts_min = ts.minute % 60
#             # await .sleep(time_to_sleep)
#             ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
#             ohlcv = ohlcv[:-1]  # drop last candle as it is not full
#             if len(ohlcv):
#                 cand_minutes = [datetime.fromtimestamp(candle[0] / 1000).minute for candle in ohlcv]
#                 use_idx = cand_minutes.index(use_ts_min)
#                 first_candle = ohlcv[use_idx]
#                 # datetime = exchange.iso8601(first_candle[0])[:-5]  # remove .000Z from end of ts
#                 # data[symbol].append([datetime, exchange.id, symbol, first_candle[1:]])
#                 # print(datetime, exchange.id, symbol, first_candle[1:])
#                 first_candle[0] = first_candle[0] / 1000
#                 row = first_candle  # [datetime] + first_candle[1:]
#                 exchange_name = exchange.name.upper().replace(' ', '_')
#                 save_symbol = f'{exchange_name}_{symbol}'
#                 db.add_single_no_verify(row, symbol=save_symbol, tf=timeframe)
#         except Exception as e:
#             print(ts, exchange, symbol, type(e).__name__, str(e))
#
#
# if __name__ == '__main__':
#     # exchange = ccxt.binance({'enableRateLimit': True})
#     db = Persistence()
#     timeframe = '1m'
#     limit = 2
#     exchanges = [ccxt.binance({'enableRateLimit': True}),
#                  ccxt.kucoin({'enableRateLimit': True}),
#                  ccxt.mexc({'enableRateLimit': True}),
#                  ccxt.coinex({'enableRateLimit': True}), ]  # ccxt.bybit(),  no btc
#     coins = [c + '/USDT' for c in COINS]
#     coins_set = set(coins)
#     exchanges_symbols = []
#     # Generate exchange / symbol pairs, test whenever it has, if not use other.
#     for exchange in exchanges:
#         print(exchange.name)
#         exchange.fetch_ohlcv('BTC/USDT', timeframe, limit=1)  # in order to get symbols, must create a call
#         supported_symbols = exchange.symbols
#         symbols = [c for c in coins_set if c in supported_symbols]
#         for sym in symbols:
#             coins_set.remove(sym)
#             exchanges_symbols.append((exchange, sym))
#             exchange_name = exchange.name.upper().replace(' ', '_')
#             sym = f'{exchange_name}_{sym}'
#             db.create(sym, timeframe)
#         if len(coins_set) == 0:
#             break
#     if len(coins_set) > 0:
#         print('Not all coins are being monitored! ::', coins_set)
#     print(exchanges_symbols)
#     for exchange, symbol in exchanges_symbols:
#         fetch_ohlcv(db, exchange, symbol, timeframe, limit)
#     print()
