import os
from cryptoUtils.DataProvider import DataProvider
import pandas as pd
from cryptoUtils.data_columns import COINS, HOURLY_COLS

data_path = os.path.join(os.getcwd(), 'resources.nosync')

coins = COINS
hourly_cols = HOURLY_COLS
start_date = '2022-03-26'

hourly_provider = DataProvider(start_date=start_date, path=os.path.join(data_path, 'data_hourly'), cols=hourly_cols,
                               convert_to_isr=False)

df = hourly_provider.serve()
last_update_cols = [f'{coin}_LASTUPDATE' for coin in coins]

df = df[last_update_cols]
df = df[df.index > '2022-04-09']

for col in last_update_cols:
    df[col] = pd.to_datetime(df[col], unit='s')

tolerance_seconds_future = 0
tolerance_minutes_past = 15
print('-' * 20, 'hourly-timestamp-diff', '-' * 40)
print(f'start: \t{df.index[0]}')
print(f'end: \t{df.index[-1]}')
print(f'tolerance_seconds_future for the future = {tolerance_seconds_future}')
print(f'tolerance_minutes_past for the past = {tolerance_minutes_past}')
# time diff..
print_rows = False
for col in last_update_cols:
    df[col] = df.index - df[col]
    # check data not from the future (timestamp is greater than request time)
    future_col = col + '_is_future'
    future_col_s = df[col].dt.total_seconds() >= 0
    if not future_col_s.all():
        future_rows = future_col_s[~future_col_s].index
        print(f'There are {len(future_rows)}/{len(df)} in coin={col} from the future(important for hourly volume')
        if print_rows:
            print(future_rows)
    past_col = col + '_is_past'
    past_col_s = df[col].dt.total_seconds() < 60 * tolerance_minutes_past
    if not past_col_s.all():
        past_rows = past_col_s[~past_col_s].index
        avg_min = df[col].dt.total_seconds().loc[past_rows].mean() / 60
        print(
            f'There are {len(past_rows)}/{len(df)} in coin={col} from the PAST, AVG_DIFF= {round(avg_min, 1)} mintues')
        if print_rows:
            print(past_rows)

    # assert (df[col].dt.total_seconds() >= -1).all(), f'There is time in coin={col} from the future(important for hourly volume'
    # # check if update that is too late
    # tolerance_minutes = 30
    # assert (df[col].dt.total_seconds() < 60 * tolerance_minutes).all(), f'There is time in coin={col} from the PAST(important for hourly volume'
# print(df[last_update_cols].tail())
