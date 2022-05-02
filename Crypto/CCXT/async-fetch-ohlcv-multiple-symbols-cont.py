# -*- coding: utf-8 -*-
import os
import sys
from asyncio import get_event_loop, gather

# -----------------------------------------------------------------------------
from Crypto.DataProcessing.data_consts import COINS
from Nasdaq.Persistence import Persistence

# -----------------------------------------------------------------------------

import ccxt.async_support as ccxt  # noqa: E402

print('CCXT Version:', ccxt.__version__)

# -----------------------------------------------------------------------------
import pandas as pd
import asyncio
from datetime import datetime, timezone
import random

df_cols = ['ts', 'open', 'high', 'low', 'close', 'volume']


# TODO: fix here if limit sync is too large, to batch fetch over time...
# Async fetch rows to db, ts is always set to be 1 min before current ts. as it waits for a whole candle to be completed.
async def fetch_ohlcv_sync_with_db(db, exchange, symbol, timeframe, ts):
    exchange_name = exchange.name.upper().replace(' ', '_')
    save_symbol = f'{exchange_name}_{symbol}'
    db_latest_ts = db.get_latest_ts(save_symbol, timeframe)
    limit_sync_rows = ((ts - db_latest_ts) // 60) + 1
    fetch_limit = 1000
    if limit_sync_rows > fetch_limit:
        raise Exception('Cannot fetch so far away')
    # print(save_symbol, 'fetching', limit_sync_rows, 'rows', f'db_latest_ts={db_latest_ts}, ts={ts}')
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=None, limit=limit_sync_rows)
    if len(ohlcv):
        df = pd.DataFrame(ohlcv, columns=df_cols)
        df['ts'] = (df['ts'] / 1000).astype(int)
        df = df.set_index('ts')
        # print('Fetched df:', db_latest_ts, df.index.min(), df.index.max())
        # filter df by latest ts in db and 1 min before from time now
        df_sync = df[(df.index > db_latest_ts) & (df.index <= ts)]
        print(
            f'{save_symbol} Saving {len(df_sync)} into db_latest:{db_latest_ts}, dfmin:{df_sync.index.min()}, dfmax:{df_sync.index.max()}')
        db.add(df_sync, save_symbol, timeframe)


async def fetch_ohlcv_forever_retry(db, exchange, symbol, timeframe):  # always take current -1
    while True:
        # this function will update exchange if db is updated atleast of 1000 candles before that.
        total_n_tries = 30
        n_tries = 0
        wait_tolerance = 3
        utc_now = datetime.utcnow()
        time_to_sleep = 60 - utc_now.second + wait_tolerance  # + random.randint(0, random_sec_to_wait)  # randomize acc time to reduce chance for ddos protection
        ts = round(utc_now.replace(tzinfo=timezone.utc).timestamp())
        await asyncio.sleep(time_to_sleep)
        while n_tries < total_n_tries:
            try:
                await fetch_ohlcv_sync_with_db(db, exchange, symbol, timeframe, ts)
                break
            except Exception as e:
                print(utc_now, exchange, symbol, f'Failed after {n_tries}/{total_n_tries}', type(e).__name__, str(e))
                n_tries += 1
                await asyncio.sleep(1)

        if n_tries > total_n_tries:
            break
    print(f'{utc_now} {exchange} {symbol} Failed over {total_n_tries} times, exiting....')


# TODO:
#  Solver kucoin async
#  [Kucoin] {"code":"429000","msg":"Too Many Requests"}. Able to ignore this error and prevent DDOS protection
#  https://github.com/freqtrade/freqtrade/issues/5700

async def main():
    # exchange = ccxt.binance({'enableRateLimit': True})
    db_path = '/Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto/ccxt_1m.db'
    db = Persistence(db_path)
    timeframe = '1m'
    exchanges = [ccxt.binance({'enableRateLimit': True}),
                 ccxt.kucoin({'enableRateLimit': True}),
                 ccxt.mexc({'enableRateLimit': True}),
                 ccxt.coinex({'enableRateLimit': True}), ]  # ccxt.bybit(),  no btc

    from Crypto.ccxt_utils import exchance_symbol_pairs

    # map exchange name to their correspond exchanges
    exchanges_symbols = [(exchanges[list(map(lambda ex: ex.name.lower(), exchanges)).index(exchange_name)], symbol) for
                         exchange_name, symbol in exchance_symbol_pairs]
    exchanges_symbols = exchanges_symbols  # [5:6]
    # print(exchanges_symbols)
    loops = [fetch_ohlcv_forever_retry(db, exchange, symbol, timeframe) for exchange, symbol in exchanges_symbols]
    await gather(*loops)
    for exchange in exchanges:
        await exchange.close()
    print()


loop = get_event_loop()
loop.run_until_complete(main())
