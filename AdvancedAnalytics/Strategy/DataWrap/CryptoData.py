from Crypto.DataProcessing.DataProvider import DataProvider
from Crypto.ccxt_utils import get_candles_from_db, exchance_symbol_pairs, get_coins
from Nasdaq.Persistence import Persistence
from .ProviderData import ProviderData
from Indicators import CandleStick
from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
from Crypto.DataProcessing.data_utils import get_data_providers, prepare_data


# from Crypto.DataProcessing.data_utils import attach_volume_to_data


class CryptoData(ProviderData):
    def __init__(self, df_prices, df_agg, symbols):
        self.df_prices = df_prices
        self.df_agg = df_agg
        self.symbols = symbols
        self.name = 'Crypto'

    def get_data(self, coin, tf):
        df_ohlc = CandleStick(tf).calc(self.df_prices[coin])
        # df_ohlc = attach_volume_to_data(self.df_agg, coin, tf, df_ohlc)
        return df_ohlc

    def get_symbols(self):
        return self.symbols

    def get_latest_ts(self):
        return self.df_prices.index[-1]

    @staticmethod
    def get_wrapper():
        providers = get_data_providers()
        df_prices, df_agg = prepare_data(providers, START_DATA_DATE)
        data_wrapper = CryptoData(df_prices, df_agg, COINS)
        return data_wrapper


class CryptoDataLive(ProviderData):
    def __init__(self, symbols, start_ts=None, start_date=None):
        # self.symbols = symbols
        self.symbols = symbols
        self.name = 'Crypto'
        self.lastest_ts = -1
        self.start_ts = start_ts
        self.start_date = start_date
        db_path = '/Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto/ccxt_1m.db'
        self.db = Persistence(db_path)
        self._data = {}

    def get_data(self, coin, tf):
        cache_name = f'{coin}{tf}'
        if cache_name in self._data:
            return self._data[cache_name]
        else:
            print(cache_name, 'Fetching from db..')
            data = get_candles_from_db(self.db, coin, tf, self.start_ts, self.start_date)
            self._data[cache_name] = data
            return data

    def get_symbols(self):
        return self.symbols

    def get_latest_ts(self):
        # self.lastest_ts = self.price_provider.serve().index[-1]
        return self.lastest_ts

    @staticmethod
    def get_wrapper(start_ts=None, start_date=None):
        if start_date and start_ts:
            raise ValueError('Only one start can be set.')
        coins = get_coins()
        data_wrapper = CryptoDataLive(coins, start_ts, start_date)
        return data_wrapper
