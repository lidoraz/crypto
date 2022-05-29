import os

from Data import CryptoData

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(root)
print(os.getcwd())
print(root)
from datetime import datetime, timedelta

# ------------------------------------------------------------------------
from Test.Cupnhandle import find_cupnhandle_and_show_on_data

tf = '1H'
print('Usually cupnhandle spans from 7 weeks to a year')
print('tf =', tf)
# filter_datetime = adjust_plot_start_datetime(tf)
start_date = str((datetime.now() - timedelta(days=10)).date())

provider = CryptoData.get_wrapper(live=False, start_date=start_date)
coins = provider.get_symbols()

col = 'close'
print('finding cup n handles...')
for coin in coins:
    print(coin)
    df = provider.get_data(coin, tf)
    # df_ohlcv = get_candles_from_db(db, coin, tf, start_date=start_date)
    # better to use values lower than 0.04, the less the more precise
    find_cupnhandle_and_show_on_data(coin, df, col='close', cupnhandle_treshold=0.035)
