from .ProviderData import ProviderData
import pandas as pd
from Nasdaq.data_utils import get_data_nasdaq
from Nasdaq.symbols import NASDAQ_PREPATH, nasdq_100


class NasdaqData(ProviderData):
    def __init__(self, symbols, prepath: str, start_date: str):
        self.prepath = prepath
        self.start_date = start_date
        self.symbols = symbols
        self.name = 'Nasdaq'

    def get_data(self, symbol, tf):
        tf_days = pd.to_timedelta(tf).days
        if tf_days == 0:
            raise ValueError('Only supports daily data or higher intervals')
        df_ohlcv = get_data_nasdaq(self.prepath + symbol + '_10y.csv', tf_days, filter_ts=False)
        df_ohlcv = df_ohlcv[df_ohlcv.index > pd.to_datetime(self.start_date)]
        return df_ohlcv

    def get_symbols(self):
        return self.symbols

    @staticmethod
    def get_wrapper(start_date: str):
        symbols = nasdq_100[1:10]
        data_wrapper = NasdaqData(symbols, NASDAQ_PREPATH, start_date=start_date)
        return data_wrapper
