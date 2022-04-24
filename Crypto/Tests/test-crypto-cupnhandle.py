from AdvancedAnalytics.Cupnhandle import find_cupnhandle_and_show_on_data
from Crypto.DataProcessing.data_utils import get_data_providers, prepare_data
from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
from Indicators import CandleStick

import os

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)
# ------------------------------------------------------------------------
tf = '1H'
print('Usually cupnhandle spans from 7 weeks to a year')
print('tf =', tf)
# filter_datetime = adjust_plot_start_datetime(tf)
providers = get_data_providers()
df_prices, df_agg = prepare_data(providers, START_DATA_DATE)

# coin = 'ETH'
col = 'close'
print('finding cup n handles...')
for coin in COINS:
    df = CandleStick(tf).calc(df_prices[coin])
    find_cupnhandle_and_show_on_data(coin, df, col='close', cupnhandle_treshold=0.03)
