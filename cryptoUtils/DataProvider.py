# This class reads all relevant csv files,
# update_and_serve updates relevant data points and serves a df
import pandas as pd
from datetime import datetime
import os

TIME_CONV = "%Y-%m-%dT%H:%M:%S"


class DataProvider:
    """
    This class reads all relevant csv files,
    update_and_serve efficiently updates relevant data points and serves a df
    """

    def __init__(self, start_date, path, cols, convert_to_isr=True):
        if isinstance(start_date, pd.Timestamp):
            start_date = str(start_date.date())
        self.start_date = start_date
        self.path = path
        self.cols = cols
        self.convert_to_isr = convert_to_isr
        self.li_data = []
        self.li_file = sorted([f for f in self._get_files() if f >= start_date])
        print(f'From: {self.li_file[0]}, To: {self.li_file[-1]}')
        self._read_csv_and_append_multi(self.li_file)

    def serve(self):
        self._update()
        return self._serve()

    def _update(self):
        curr_date = str(datetime.utcnow().date())
        last_date_in_data = self.li_file[-1]
        if curr_date == last_date_in_data:
            self._modify_latest()
        elif curr_date > last_date_in_data:
            self._add_if_exists()
        else:
            raise ValueError('curr_date lower than current file')

    def _serve(self):
        df = pd.concat(self.li_data, axis=0, ignore_index=True)
        df.columns = ['timestamp'] + self.cols
        if self.convert_to_isr:  # convert to ISR time zone
            df['timestamp'] = pd.to_datetime(df['timestamp'], format=TIME_CONV, utc=True).dt.tz_convert('Israel')
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format=TIME_CONV, utc=False)
        df = df.set_index('timestamp', drop=True)
        return df

    def _add_if_exists(self):
        list_files = self._get_files()
        list_files = [f for f in list_files if f not in self.li_file]
        print('adding:', list_files)
        self._read_csv_and_append_multi(list_files)

    def _read_csv_and_append_multi(self, list_files):
        for f in list_files:
            df = self._read_csv_safe(f)
            if df is not None:
                self.li_data.append(df)

    def _modify_latest(self):
        self.li_data[-1] = self._read_csv_safe(self.li_file[-1])

    def _get_files(self):
        return [f.split('.')[0] for f in os.listdir(self.path) if f.endswith('.csv')]

    def _read_csv_safe(self, file):
        # safe read because there is a case where autoupdate has opened a file but did not write to it yet.
        full_path = os.path.join(self.path, file + '.csv')
        try:
            if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
                return None
        except OSError:
            print('something is wrong when loading csvs.. OSERROR')
            return None
        return pd.read_csv(full_path, index_col=None, header=None)

#     def _is_time_updated(self, time_now, treshold_seconds=90):
#     return (datetime.utcnow() - time_now.tz_convert(None)).total_seconds() < treshold_seconds


# function that combines loading data into one, returns two dfs.
# Checks different important like TODO: is_ok_time_diff:
# %%time
# def is_time_updated(time_now, treshold_seconds=90):
#     return (datetime.utcnow() - time_now.tz_convert(None)).total_seconds() < treshold_seconds
#
# def load_dataframes(coins, hourly_cols, start_date):
#     df_prices = load_data('data', coins, start_date)
#     df_hourly = load_data('data_hourly', hourly_cols, start_date)
#     df_hourly = df_hourly.resample('1H', closed='right').pad() # resample to nearest cieling hour
#     is_ok_time_diff = len(df_prices[list(df_prices.reset_index()['timestamp'].diff().dt.total_seconds() > 120)]) == 0
#     assert is_ok_time_diff , 'There are instances with larger time diff'
#     print(df_prices.index[-1])
#     if not is_time_updated(df_prices.index[-1]):
#         print('ALERT- database not updated, wait or check process')
#     return df_prices, df_hourly
#
# df_prices, df_hourly = load_dataframes(coins, hourly_cols, start_date)
# print(df_prices.shape, df_hourly.shape)

# Depreceted, used with different process auto_update.py
# can improve this and load only current day file
# need to be implemented with a class
# def load_data(dir_name, cols, start_date=None, convert_to_isr=True):
#     li = []
#     list_files = [f for f in os.listdir(dir_name) if f.endswith('.csv')]
#     if start_date is not None:
#         list_files = [f for f in list_files if f >= start_date]
#
#     for filename in sorted(list_files):
#         df = pd.read_csv(os.path.join(dir_name, filename), index_col=None, header=None)
#         li.append(df)
#
#     df = pd.concat(li, axis=0, ignore_index=True)
#     df.columns = ['timestamp'] + cols
#     # convert to ISR time zone
#     if convert_to_isr:
#         df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert('Israel')
#     df = df.set_index('timestamp', drop=True)
#     return df
