import pandas as pd
import numpy as np

from AStock.symbols import nasdq_100
from AStock.yahoo_finance import get_from_yfinance_now
from Plots.plotly_fig import get_updated_fig
import os

intervals = [('1', '1min'),
             ('5', '5min'),
             ('15', '15min'),
             ('H', '1h'),
             ('D', '1D'),
             ('W', '7D'),
             ('M', '30D'),
             ('Y', '365D')]

symbol = nasdq_100[3]
interval_p = intervals[5]
interval_set = interval_p[1]
print(symbol, interval_p)
df_ohlcv = get_from_yfinance_now(symbol, interval_set, tz='Israel')
if not len(df_ohlcv):
    raise ValueError('No data')
df_ohlcv.columns = [c.lower() for c in df_ohlcv.columns]
if pd.to_timedelta(interval_set).days > 1:
    interval_set = '1' + interval_p[0]
    df_ohlcv = resample_ohlcv_higher_1d(df_ohlcv, interval_set)
df_ohlcv.attrs['interval'] = interval_set
fig = get_updated_fig(df_ohlcv, lookahead=14, xy_limit=False)

fig.update_layout(title=symbol, title_y=0.99, title_x=0.5)
fig.show()
