from DataProcessing.data_consts import COINS, HOURLY_COLS, START_DATA_DATE
import os
import pandas as pd
# from Plots.plot_utils import START_DATA_DATETIME
from DataProcessing.data_utils import get_crypto_olhcv, get_data_providers
from Plots.plotly_fig import get_updated_fig

data_path = os.path.join(os.getcwd(), 'resources.nosync')

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = ['2Min', '5Min', '15Min', '1H', '4H', '1D']
coin = COINS[1]
resample = resample_keywords[1]
start_date = START_DATA_DATE  # '2022-03-26'
print(start_date, coin, resample)

providers = get_data_providers()

filter_date = pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')
df_ohlcv = get_crypto_olhcv(coin, resample, providers, filter_date, is_volume_hourto=True)
fig = get_updated_fig(df_ohlcv, xy_limit=True)
fig.show()
