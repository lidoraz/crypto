# from Crypto.DataProcessing.data_consts import COINS, HOURLY_COLS, START_DATA_DATE
from Utils import Persistence
from Crypto.ccxt_utils import _resample_from_ohlcv
from Crypto.symbols import exchance_symbol_pairs, DB_PATH
import os
from Plots.plotly_fig import get_updated_fig

coins = [c[1].split('/')[0] for c in exchance_symbol_pairs]

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)
# ------------------------------------------------------------------------

data_path = os.path.join(os.getcwd(), 'resources.nosync')

# hourly_cols = HOURLY_COLS
resample_keywords = ['2Min', '5Min', '15Min', '1H', '4H', '1D']
coin = coins[1]
resample = resample_keywords[-3]
# start_date = START_DATA_DATE  # '2022-03-26'
# print(start_date, coin, resample)

print(coin, resample)
db = Persistence(DB_PATH)
exchange_str = 'binance'
symbol_str = f'{coin}/USDT'
db_symbol = f'{exchange_str}_{symbol_str}'.upper()
df = db.get_df(db_symbol, '1m')
df_ohlcv = _resample_from_ohlcv(df, resample)
# providers = get_data_providers()

# filter_date = pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')
# filter_date = START_DATA_DATE
# df_ohlcv = get_crypto_olhcv(coin, resample, providers, filter_date, is_volume_hourto=True)
fig = get_updated_fig(df_ohlcv, xy_limit=True)
fig.show()
