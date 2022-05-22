import pandas as pd
import asyncio
from datetime import datetime, timezone
from asyncio import get_event_loop, gather
from Utils import Persistence
import ccxt.async_support as ccxt
from symbols import exchange_symbol_pairs, DB_PATH
import time

print('Async crawler for selected symbols, creates table and fetches history')
print('async-fetch-ohlcv-multiple-symbols-cont')

print('CCXT Version:', ccxt.__version__)

# TODO: Move ExchangeNotAvailable to a seperate catch such that it will handle times where there is no internet.
# not sure if this is needed, just increase the ntries to something higher.
df_cols = ['ts', 'open', 'high', 'low', 'close', 'volume']
ccxt_errors = (ccxt.errors.RateLimitExceeded,
               ccxt.errors.BadRequest,
               ccxt.errors.RequestTimeout,
               ccxt.errors.ExchangeError,
               ccxt.errors.ExchangeNotAvailable)


FETCH_LIMIT = 1000
# START_TS = 1651000000  # 1646000000  # Sunday, February 27, 2022
time_delta_sec_month = 60 * 60 * 24 * 30
START_TS = int(time.time()) - time_delta_sec_month * 3  # Take two month before from script start
N_TRIES_LIMIT = 100


# binary search
async def find_first_symbol_ohlcv(exchange, symbol, timeframe, start_ts_ms, curr_ts_ms):
    print('Finding first ts for:', symbol)
    max_val = curr_ts_ms // 1000
    min_val = start_ts_ms // 1000
    mid = start_ts_ms
    n_tries = 1
    while max_val - min_val > 1 and n_tries <= N_TRIES_LIMIT:
        try:
            mid = min_val + (max_val - min_val) // 2
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=mid * 1000, limit=1)
            if ohlcv:  # move back
                max_val = mid
            else:  # move forward
                min_val = mid
            # print(min_val, mid, max_val, max_val - min_val)
            await asyncio.sleep(1)
        except ccxt_errors as e:
            print('search', exchange, symbol, f'Failed after {n_tries}/{N_TRIES_LIMIT}', type(e).__name__, str(e))
            await asyncio.sleep(1)
            n_tries += 1
    if n_tries > N_TRIES_LIMIT:
        print('problem in searching first ts....', exchange, symbol)
    print(f'start ts for {symbol}', mid)
    return mid * 1000


async def fetch_ohlcv_history_to_db(db, exchange, symbol, timeframe, curr_ts, db_latest_ts):
    exchange_name = exchange.name.upper().replace(' ', '_')
    save_symbol = f'{exchange_name}_{symbol}'

    start_ts = max(START_TS, db_latest_ts)
    start_ts_loop_ms = start_ts * 1000
    end_ts_loop_ms = 0
    n_tries = 1
    # subtract few min from curr_ts, so next loop it will get to main fetch
    curr_ts_ms = (curr_ts - 60 * 10) * 1000
    while start_ts_loop_ms < curr_ts_ms and n_tries <= N_TRIES_LIMIT:
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=start_ts_loop_ms, limit=FETCH_LIMIT)
            # TODO: something is not working again with kucoin , it returns empty array but it is in range... really strange.
            #  Update: Kucoin is crap, they don't allow to fetch history so far away.
            # print('ohlcv****', ohlcv)
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=df_cols)
                df['ts'] = (df['ts'] / 1000).astype(int)
                df = df.set_index('ts')
                df_sync = df[(df.index >= start_ts) & (df.index < curr_ts)]
                db.add(df_sync, save_symbol, timeframe)

                end_ts_loop_ms = df.index[-1] * 1000
                # print(len(df_sync), start_ts_loop_ms, end_ts_loop_ms, curr_ts_ms, fetch_limit)
                start_ts_loop_ms = end_ts_loop_ms
            else:
                # print('failed', start_ts_loop_ms, symbol)
                # start_ts_loop_ms = start_ts_loop_ms + 60 * 1000
                start_ts_ms = start_ts * 1000
                start_ts_loop_ms = await find_first_symbol_ohlcv(exchange, symbol, timeframe, start_ts_ms, curr_ts_ms)
                await asyncio.sleep(1)
        except ccxt_errors as e:
            print(start_ts_loop_ms, exchange, symbol, f'History failed after {n_tries}/{N_TRIES_LIMIT}',
                  type(e).__name__,
                  str(e))
            await asyncio.sleep(1)
            n_tries += 1

    if n_tries > N_TRIES_LIMIT:
        print(start_ts_loop_ms, exchange, symbol, f'History failed after {n_tries}/{N_TRIES_LIMIT}!!')
        # raise Exception(f'Could not fetch history... {symbol}')
    start_dt = pd.to_datetime(end_ts_loop_ms, unit='ms', utc=True)
    end_dt = pd.to_datetime(curr_ts_ms, unit='ms', utc=True)
    print('Inserted Batch data', save_symbol, start_dt, end_dt)


# TODO: fix here if limit sync is too large, to batch fetch over time...
# Async fetch rows to db, ts is always set to be 1 min before current ts. as it waits for a whole candle to be completed.
async def fetch_ohlcv_sync_with_db(db, exchange, symbol, timeframe, ts):
    exchange_name = exchange.name.upper().replace(' ', '_')
    save_symbol = f'{exchange_name}_{symbol}'
    db_latest_ts = db.get_latest_ts(save_symbol, timeframe)
    if db_latest_ts == -1:
        db.create(save_symbol, timeframe)
    limit_sync_rows = ((ts - db_latest_ts) // 60) + 1

    if limit_sync_rows > FETCH_LIMIT:
        if db_latest_ts == -1:
            print(f'fetching history for {symbol}, no rows at all db_latest_ts', db_latest_ts)
        else:
            print(f'fetching history for {symbol}, missing rows: {limit_sync_rows}, db_latest_ts:{db_latest_ts}')
        await fetch_ohlcv_history_to_db(db, exchange, symbol, timeframe, ts, db_latest_ts)
        return
    # print(save_symbol, 'fetching', limit_sync_rows, 'rows', f'db_latest_ts={db_latest_ts}, ts={ts}')
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=None, limit=FETCH_LIMIT)
    if len(ohlcv):
        df = pd.DataFrame(ohlcv, columns=df_cols)
        df['ts'] = (df['ts'] / 1000).astype(int)
        df = df.set_index('ts')
        # filter df by latest ts in db and 1 min before from time now
        df_sync = df[(df.index > db_latest_ts) & (df.index <= ts)]
        if len(df_sync):
            to_dt = datetime.fromtimestamp
            if len(df_sync) > 1:
                print(f'{save_symbol}\tSaving {len(df_sync)} records into db({to_dt(db_latest_ts)})'
                      f'\trecords: ({to_dt(df_sync.index.min())},{to_dt(df_sync.index.max())})')
            else:
                print(f'{save_symbol}\tSaving {len(df_sync)} records into db({to_dt(db_latest_ts)})'
                      f'\trecord: {to_dt(df_sync.index.min())}')
            db.add(df_sync, save_symbol, timeframe)


async def fetch_ohlcv_forever_retry(db, exchange, symbol, timeframe):  # always take current -1
    print(f'Starting to fetch forever: From={exchange.name} symbol={symbol}')
    while True:
        # this function will update exchange if db is updated atleast of 1000 candles before that.
        n_tries = 1
        wait_sec = 0
        utc_now = datetime.utcnow()
        time_to_sleep = 60 - utc_now.second + wait_sec  # + random.randint(0, random_sec_to_wait)  # randomize acc time to reduce chance for ddos protection
        ts = round(utc_now.replace(tzinfo=timezone.utc).timestamp())
        await asyncio.sleep(time_to_sleep)  # time_to_sleep
        while n_tries <= N_TRIES_LIMIT:
            try:
                await fetch_ohlcv_sync_with_db(db, exchange, symbol, timeframe, ts)
                break
            except ccxt_errors as e:
                print(utc_now, exchange, symbol, f'Failed after {n_tries}/{N_TRIES_LIMIT}', type(e).__name__, str(e))
                n_tries += 1
                await asyncio.sleep(1)
        if n_tries > N_TRIES_LIMIT:
            break
    print(f'{utc_now} {exchange} {symbol} Failed over {N_TRIES_LIMIT} times, exiting....')
    return -1


# Saving closed candles only unfinished candles are dropped.
async def main():
    db_path = DB_PATH
    db = Persistence(db_path)
    timeframe = '1m'
    exchanges = [ccxt.binance({'enableRateLimit': True}),
                 ccxt.kucoin({'enableRateLimit': True}),
                 ccxt.mexc({'enableRateLimit': True}),
                 ccxt.coinex({'enableRateLimit': True}), ]  # ccxt.bybit(),  no btc

    def treat_ex_name(x):
        x = x.lower().replace(' ', '_')
        return x

    db.create_multiple_tables(exchange_symbol_pairs, timeframe)

    # map exchange name to their correspond exchanges
    exchanges_symbols = [
        (exchanges[list(map(lambda ex: treat_ex_name(ex.name), exchanges)).index(exchange_name)], symbol) for
        exchange_name, symbol in exchange_symbol_pairs]
    # exchanges_symbols = exchanges_symbols  # [5:6]
    # print(exchanges_symbols)
    loops = [fetch_ohlcv_forever_retry(db, exchange, symbol, timeframe) for exchange, symbol in exchanges_symbols]
    await gather(*loops)
    for exchange in exchanges:
        await exchange.close()
    print()


loop = get_event_loop()
loop.run_until_complete(main())
