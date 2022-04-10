import pandas as pd
from datetime import datetime
import os
import plotly.graph_objects as go
import numpy as np
import json

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime


def get_candle_stick(df_coin):
    trace = go.Candlestick(x=df_coin.index,
                           open=df_coin.open,
                           high=df_coin.high,
                           low=df_coin.low,
                           close=df_coin.close,
                           name='Candle',
                           )
    return trace


def get_pct_change(coin, df_hourly):
    pct_hourly = df_hourly[f'{coin}_CHANGEPCTHOUR']
    pct_color = pct_hourly.apply(lambda x: 'Green' if x > 0 else 'Red')
    trace = go.Bar(x=df_hourly.index, y=pct_hourly, marker_color=pct_color)
    return trace


def get_pct_change_c(df_prices):
    # resample('1H', closed='right').ffill()
    close_pct = df_prices.close.pct_change() * 100
    #     df_coin = df_coin.copy()
    #     df_coin['close_pct'] = df_coin.close.pct_change() * 100
    #     close_pct = df_prices[coin]['close'].rolling("1H").pct_change() * 100
    close_pct_color = close_pct.apply(lambda x: 'Green' if x > 0 else 'Red')
    trace = go.Bar(x=close_pct.index, y=close_pct, marker_color=close_pct_color, name='PCT1HChange')
    return trace


def get_volume(volume):
    # VOLUMEHOURTO
    # VOLUMEHOUR
    return go.Bar(x=volume.index, y=volume, name='Volume')


def get_MAD(coin_ohlc, pts, col='close', color='purple'):
    ra = coin_ohlc[col].rolling(pts).mean()
    # visible='legendonly' - appears but grayed out
    return go.Scatter(x=ra.index, y=ra, name=f'MA({pts})', line_color=color, line_width=1)


def get_EMA(coin_ohlc, pts, col='close', color='orange'):
    ema = coin_ohlc[col].ewm(span=pts).mean()  # closed to the right!!
    #     ra = coin_ohlc['close'].resample(f'{days}D').mean()
    return go.Scatter(x=ema.index, y=ema, name=f'EMA({pts})', line_color=color)


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])


def get_fib_seq(length):
    fib_i = 0
    next_fib_i = 1
    fib_seq = []
    while fib_i < length:
        fib_seq.append(fib_i)
        tmp = fib_i
        fib_i = fib_i + next_fib_i
        next_fib_i = tmp
    if len(fib_seq) > 1:
        fib_seq.remove(1)
    return fib_seq


def FMA(data):
    fib_seq = get_fib_seq(len(data))
    return data[::-1].iloc[fib_seq][::-1].mean()


def get_FibMAD(coin_ohlc, pts, col='close', color='cyan'):
    fma = coin_ohlc[col].rolling(pts).apply(FMA)
    return go.Scatter(x=fma.index, y=fma, name=f'FibMA({pts})', line_color=color)


# def calc_rsis(df_coin, n_rsis, col='close'):
#     for n_rsi in n_rsis:
#         calc_rsi(df_coin, n_rsi, col=col)
#


def calc_rsi(df_coin, n, col='close'):
    if n >= len(df_coin):  # fail safe in case of an error
        n = len(df_coin) - 1

    # https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe
    def rma(x, n, y0):
        a = (n - 1) / n
        ak = a ** np.arange(len(x) - 1, -1, -1)
        return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a ** np.arange(1, len(x) + 1)]

    df = df_coin.copy()
    df['change'] = df[col].diff()
    df['gain'] = df.change.mask(df.change < 0, 0.0)
    df['loss'] = -df.change.mask(df.change > 0, -0.0)
    df['avg_gain'] = rma(df.gain[n + 1:].to_numpy(), n, np.nansum(df.gain.to_numpy()[:n + 1]) / n)
    df['avg_loss'] = rma(df.loss[n + 1:].to_numpy(), n, np.nansum(df.loss.to_numpy()[:n + 1]) / n)
    df['rs'] = df.avg_gain / df.avg_loss
    df['rsi_n'] = 100 - (100 / (1 + df.rs))
    return df['rsi_n']


def get_RSI_from_calucated(ra, pts, color='white'):
    return go.Scatter(x=ra.index, y=ra, name=f'RSI({pts})', line_color=color, line_width=1)


def get_RSI(df_coin, pts, col='close', color='white'):
    ra = calc_rsi(df_coin, pts, col=col)
    return go.Scatter(x=ra.index, y=ra, name=f'RSI({pts})', line_color=color, line_width=1)
