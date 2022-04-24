import pandas as pd
from Crypto.DataProcessing.DataProvider import DataProvider
from Crypto.DataProcessing.data_consts import COINS, HOURLY_COLS
import os

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)
# ------------------------------------------------------------------------

tolerance_seconds_future = 0
tolerance_minutes_past = 15
verbose = 0

data_path = os.path.join(os.getcwd(), 'resources.nosync')
df = DataProvider(start_date='2022-03-26', path=os.path.join(data_path, 'data_hourly'), cols=HOURLY_COLS,
                  convert_to_isr=False).serve()
last_update_cols = [f'{coin}_LASTUPDATE' for coin in COINS]
df = df[last_update_cols]
df = df[df.index > '2022-04-08 20:00:00']
for col in last_update_cols:
    df[col] = pd.to_datetime(df[col], unit='s')

print('-' * 20, 'hourly-timestamp-diff', '-' * 40)
print(f'start: \t{df.index[0]}')
print(f'end: \t{df.index[-1]}')
print(f'tolerance_seconds_future for the future = {tolerance_seconds_future}')
print(f'tolerance_minutes_past for the past = {tolerance_minutes_past}')

problematic_coins = []
for col in last_update_cols:
    coin = col.split('_')[0]
    df[col] = df.index - df[col]
    # check data not from the future (timestamp is greater than request time)
    future_col = col + '_is_future'
    future_col_s = df[col].dt.total_seconds() >= 0
    if not future_col_s.all():
        problematic_coins.append(coin)
        if verbose > 0:
            future_rows = future_col_s[~future_col_s].index
            print(f'There are {len(future_rows)}/{len(df)} in coin={col} from the future(important for hourly volume')
            if verbose > 1:
                print(future_rows)

    past_col = col + '_is_past'
    past_col_s = df[col].dt.total_seconds() < 60 * tolerance_minutes_past
    if not past_col_s.all():
        problematic_coins.append(coin)
        if verbose > 0:
            past_rows = past_col_s[~past_col_s].index
            avg_min = df[col].dt.total_seconds().loc[past_rows].mean() / 60
            print(
                f'There are {len(past_rows)}/{len(df)} in coin={col} from the PAST, AVG_DIFF= {round(avg_min, 1)} mintues')
            if verbose > 1:
                print(past_rows)

print(sorted(set(problematic_coins)))
