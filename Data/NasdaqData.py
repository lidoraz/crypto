from Data.Nasdaq.yahoo_finance import get_from_yfinance_now
from Data.Nasdaq.data_utils import get_data_nasdaq
from Data.Nasdaq.symbols import NASDAQ_PREPATH, nasdq_100
from .ProviderData import ProviderData
import pandas as pd


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

        # TODO: Test # CANT use this as like this, must use persitsance - can implement this to fetch first from yahoo if not updated.
        # df = get_from_yfinance_now(symbol, tf)
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
