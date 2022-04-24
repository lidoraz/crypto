import pandas as pd
import os
import numpy as np
from Plots.plotly_fig import get_updated_fig

prepath = 'Tests/yahoo_data/'
interval = '1D'
print('filtering to last 2 years.')
# TODO: can't easily downsample 1d into one month of OHLCV. need to find something else.
# http://techflare.blog/mastering-dataframe-how-to-aggregate-ohlcv-data-in-a-different-time-period/
data_paths = os.listdir(prepath)
f = data_paths[np.random.randint(0, len(data_paths))]
print(interval, f)
symbol = f.split('_')[0]
df = pd.read_csv(prepath + f, index_col='Date')
df.index = pd.to_datetime(df.index)
df = df[df.index > pd.to_datetime('2021-01-01')]
# df = df.resample(interval).interpolate()
df.attrs['interval'] = interval
df.columns = [c.lower() for c in df.columns]

fig = get_updated_fig(df, lookahead=14, xy_limit=False)

fig.update_layout(title=f)
fig.show()
