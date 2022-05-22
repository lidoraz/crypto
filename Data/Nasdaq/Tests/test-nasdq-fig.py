import pandas as pd
import numpy as np
from Plots.plotly_fig import get_updated_fig
import os

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)
# ------------------------------------------------------------------------
prepath = 'Nasdaq/yahoo_data/'
interval = '1D'
interval = '1W'


def resample_ohlcv_higher_1d(ohlcv, interval):
    ohlcv = pd.concat([
        ohlcv['open'].resample(interval).first(),
        ohlcv['high'].resample(interval).max(),
        ohlcv['low'].resample(interval).min(),
        ohlcv['close'].resample(interval).last(),
        ohlcv['volume'].resample(interval).sum()], axis=1)
    return ohlcv


data_paths = os.listdir(prepath)
f = data_paths[np.random.randint(0, len(data_paths))]
print(interval, f)
symbol = f.split('_')[0]
df_ohlcv = pd.read_csv(prepath + f, index_col='Date')
df_ohlcv.index = pd.to_datetime(df_ohlcv.index)
print('filtering to last 2 years.')
df_ohlcv = df_ohlcv[df_ohlcv.index > pd.to_datetime('2019-01-01')]

df_ohlcv.columns = [c.lower() for c in df_ohlcv.columns]
if pd.to_timedelta(interval).days > 1:
    df_ohlcv = resample_ohlcv_higher_1d(df_ohlcv, interval)
df_ohlcv.attrs['interval'] = interval
fig = get_updated_fig(df_ohlcv, lookahead=14, xy_limit=False)

fig.update_layout(title=f, title_y=0.99, title_x=0.5)
fig.show()
