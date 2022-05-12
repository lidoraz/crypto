from Crypto.ccxt_utils import get_candles_from_db, get_coins
from Crypto.symbols import DB_PATH
from Utils import Persistence
from .ProviderData import ProviderData, PreLoaded
import pandas as pd
import time


class CryptoData(ProviderData):
    def __init__(self, symbols, live, start_ts=None, start_date=None):
        # self.symbols = symbols
        self.symbols = symbols
        self.name = 'Crypto'
        self.live = live
        self.update_sec_every = 30
        self.start_ts = start_ts
        self.start_date = start_date
        # TODO: remove fixed path
        db_path = DB_PATH
        self.db = Persistence(db_path)
        self._data = {}
        self._lastest_data_ts = {}
        # self.diff_local_db_sec = 240  # TODO(#3323): check why difference is high, it should be atleast 1min, but not more than 2 min.

    def get_data(self, coin, tf, start_date=None):
        cache_name = f'{coin}{tf}'
        curr_ts_local = int(time.time())
        if cache_name in self._data:
            if self.live:
                ts_diff = curr_ts_local - self._lastest_data_ts[cache_name]
                if ts_diff < self.update_sec_every:  # not needed cache_name in self._lastest_data_ts and
                    # print('using cache.. ', coin, ts_diff)
                    return self._data[cache_name]
            else:
                return self._data[cache_name]
        # print(cache_name, 'Fetching from db..')
        start_date = start_date if start_date else self.start_date
        data = get_candles_from_db(self.db, coin, tf, self.start_ts, start_date)
        self._data[cache_name] = data
        curr_ts_db = data.attrs['curr_ts_db']
        diff_local_db = curr_ts_local - curr_ts_db
        self._lastest_data_ts[cache_name] = curr_ts_db
        # TODO(#3323) will not be suitable for less than 5min tf.
        # is_updated = diff_local_db < pd.to_timedelta(tf).total_seconds() / 2
        is_updated = diff_local_db < pd.to_timedelta('5min')
        if not is_updated:
            print(f'Warning {coin, tf} DB timestamp is not updated to machine time,  diff= {diff_local_db}sec')
            if self.live:
                print(f'Warning {coin, tf} ignored!')
                return None

        return data

    def get_symbols(self):
        return self.symbols

    # TODO: add option to update if update is interval is none.

    # def get_latest_ts(self):
    #     # self.lastest_ts = self.price_provider.serve().index[-1]
    #     return self.lastest_ts

    def get_preloaded(self, tfs):
        if isinstance(tfs, str):
            tfs = [tfs]
        for symbol in self.symbols:
            for tf in tfs:
                _ = self.get_data(symbol, tf)
        return PreLoaded(self._data, self.symbols)

    @staticmethod
    def get_wrapper(live, start_ts=None, start_date=None):
        if start_date and start_ts:
            raise ValueError('Only one start can be set.')
        print(f'CryptoData: {live, start_ts, start_date}')
        coins = get_coins()
        data_wrapper = CryptoData(coins, live, start_ts, start_date)
        return data_wrapper

    # # TODO: add this into code
    # @staticmethod
    # def get_offline_wrapper(time_intervals, start_ts=None, start_date=None):
    #     coins = get_coins()
    #     data_wrapper = CryptoDataLive(coins, None, False, start_ts, start_date)
    #     provider_loaded = data_wrapper.get_preloaded(time_intervals)
    #     return provider_loaded
