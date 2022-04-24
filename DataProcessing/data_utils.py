from datetime import datetime

import numpy as np
import pandas as pd
import os
from .DataProvider import DataProvider
from .data_consts import *
from Plots.plot_utils import human_format, INTERVAL_CANDLE_LOOKBACK_TABLE, INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER, \
    INTERVAL_CANDLE_LOOKBACK_LOAD_MULTIPLAYER
from .data_consts import START_DATA_DATE


def get_data_providers():
    data_path = os.path.join(os.getcwd(), 'resources.nosync')
    price_provider = DataProvider(START_DATA_DATE, os.path.join(data_path, 'data'), COINS)
    hourly_provider = DataProvider(START_DATA_DATE, os.path.join(data_path, 'data_hourly'), HOURLY_COLS)
    providers = dict(price_provider=price_provider, hourly_provider=hourly_provider)
    return providers


def prepare_data(providers, start_datetime):
    # TODO: can take strings if using: datetime.fromisoformat(start_datetime) # but still tz is missing
    print('prepare_data:: load date start:', start_datetime)
    price_provider = providers['price_provider']
    hourly_provider = providers['hourly_provider']
    df_prices = price_provider.serve()
    df_hourly = hourly_provider.serve()
    if start_datetime != START_DATA_DATE:
        df_prices = df_prices[df_prices.index.to_pydatetime() > start_datetime]
        df_hourly = df_hourly[df_hourly.index.to_pydatetime() > start_datetime]
    # is_ok_time_diff = len(df_prices[list(df_prices.reset_index()['timestamp'].diff().dt.total_seconds() > 120)]) == 0
    # assert is_ok_time_diff, 'There are instances with larger time diff'
    return df_prices, df_hourly


def get_coin_status(df_hourly, coin):
    cols = ['VOLUMEDAY', 'CHANGEPCT24HOUR', 'VOLUME24HOURTO']
    coin_cols = [f'{coin}_{col}' for col in cols]
    coin_stats = df_hourly[coin_cols].iloc[-1]  # df_hourly.index[-1]
    coin_stats = coin_stats.apply(human_format)
    stats = {k: v for k, v in zip(cols, coin_stats)}
    return stats


def get_olhc(prices, interval):
    return prices.resample(interval, closed='right').ohlc()


def get_crypto_olhcv(coin, interval, providers, start_datetime, is_volume_hourto=True):
    df_prices, df_hourly = prepare_data(providers, start_datetime)
    df_ohlc = get_olhc(df_prices[coin], interval)
    # not needed
    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats} :: agg every {interval}, Price: {df_ohlc.close.iloc[-1]}")

    df_ohlcv = attach_volume_to_data(df_hourly, coin, interval, df_ohlc, is_volume_hourto=is_volume_hourto)
    df_ohlcv.attrs['interval'] = interval
    return df_ohlcv


def attach_volume_to_data(df_hourly, coin, interval, df_ohlc, is_volume_hourto=True):
    volume_hour, volume_hourto = extract_volume(df_hourly, coin, interval)
    if is_volume_hourto:
        vol = volume_hourto
    else:
        vol = volume_hour
    vol.name = 'volume'
    df_ohlcv = df_ohlc.join(volume_hourto).dropna()
    return df_ohlcv


# TODO: since below date data became refreshed every 15 min add here is there could be a problem if data is not refreshed every 15 min (can be in rare coins)
def extract_volume(df_agg, coin, interval, cols=('VOLUMEHOUR', 'VOLUMEHOURTO')):
    # https://stackoverflow.com/questions/38666924/what-is-the-inverse-of-the-numpy-cumsum-function
    def inverse_cumsum(x):
        return np.diff(x, prepend=0)

    # interval granularity lower than 15Min
    is_lower_than_15min = False
    pre_interval = interval
    if 'Min' in interval and int(interval.split('Min')[0]) < 15:
        interval = '15Min'
        is_lower_than_15min = True
    else:
        interval = interval
    coin_cols = [f'{coin}_{col}' for col in cols]
    # before this time all volume is crap
    df_agg = df_agg[df_agg.index > pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')]

    # apply function column-by-column to the grouped
    g = df_agg[coin_cols].groupby(df_agg.index.floor('h'))
    df_cols_t = g.transform(inverse_cumsum)
    # move each index by 1 min to resample closest value.
    df_cols_t.index = df_cols_t.index + pd.to_timedelta('1Min')
    df_cols_r = df_cols_t.resample(interval, closed='right').sum()

    # TODO: fix this later, dividing missing parts and refill with avg
    if is_lower_than_15min:
        def re_divide(arr):
            return arr / 3 if len(arr) else None

        df_cols_r = df_cols_r.resample(pre_interval).apply(re_divide).fillna(method='bfill')
    # df_cols_r = df_cols_r.astype(np.int64)
    # df_cols_r.columns = ['volume', 'volumeto']
    return df_cols_r[coin_cols[0]], df_cols_r[coin_cols[1]]


def adjust_plot_start_datetime(interval_length: str, is_display=False, tz_isr=True):
    time_now = pd.to_datetime(datetime.utcnow(), utc=True)
    start_datetime = time_now.tz_convert('Israel') if tz_isr else time_now

    if interval_length in INTERVAL_CANDLE_LOOKBACK_TABLE:
        if is_display:
            delta = INTERVAL_CANDLE_LOOKBACK_TABLE[interval_length] * INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER
        else:
            delta = INTERVAL_CANDLE_LOOKBACK_TABLE[interval_length] * INTERVAL_CANDLE_LOOKBACK_LOAD_MULTIPLAYER
        filter_datetime = (start_datetime - delta)
        if filter_datetime > start_datetime:
            filter_datetime = start_datetime
        # print(f'filter_datetime = {filter_datetime}')
    else:
        filter_datetime = START_DATA_DATE
    return filter_datetime

