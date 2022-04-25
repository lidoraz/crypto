from abc import abstractmethod, ABC
from Indicators import CandleStick
import pandas as pd
from Nasdaq.data_utils import get_data_nasdaq


# from Crypto.DataProcessing.data_utils import attach_volume_to_data


class DataWrapper(ABC):

    @abstractmethod
    def get_data(self, symbol: str, tf: str):
        pass

    @abstractmethod
    def get_symbols(self):
        pass


class CryptoData(DataWrapper):
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


class NasdaqData(DataWrapper):
    def __init__(self, symbols, prepath: str, start_date: str):
        self.prepath = prepath
        self.start_date = start_date
        self.symbols = symbols
        self.name = 'Nasdaq'

    def get_data(self, coin, tf):
        df_ohlcv = get_data_nasdaq(self.prepath + coin + '_10y.csv', tf, filter_ts=False)
        df_ohlcv = df_ohlcv[df_ohlcv.index > pd.to_datetime(self.start_date)]
        return df_ohlcv

    def get_symbols(self):
        return self.symbols
