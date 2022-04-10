from DataPreprocessing.data_columns import COINS, HOURLY_COLS
import os

from Plots.plot_utils import START_DATA_DATETIME
from Plots.plotly_fig import get_updated_fig
from DataPreprocessing.DataProvider import DataProvider

data_path = os.path.join(os.getcwd(), 'resources.nosync')

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = ['5Min', '15Min', '1H', '4H', '1D']
coin = COINS[1]
resample = resample_keywords[1]
start_date = START_DATA_DATETIME  # '2022-03-26'

price_provider = DataProvider(start_date=start_date, path=os.path.join(data_path, 'data'), cols=coins)
hourly_provider = DataProvider(start_date=start_date, path=os.path.join(data_path, 'data_hourly'), cols=hourly_cols)
providers = dict(price_provider=price_provider,
                 hourly_provider=hourly_provider)
import pandas as pd

# TODO: add utility function to tz convert
filter_date = pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')  # TODO: unused
fig = get_updated_fig(providers, filter_date, resample, coin)
fig.show()
