from Indicators import CandleStick
import pandas as pd
from Nasdaq.data_utils import get_data_nasdaq


class CryptoData:
    def __init__(self, df_prices, symbols):
        self.df_prices = df_prices
        self.symbols = symbols
        self.name = 'Crypto'

    def get_data(self, coin, tf):
        # _, volume = extract_volume(df_agg=df_agg, coin=coin, interval=tf)
        df = CandleStick(tf).calc(self.df_prices[coin])
        return df


class NasdaqData:
    def __init__(self, symbols, prepath: str, start_date: str):
        self.prepath = prepath
        self.start_date = start_date
        self.name = 'Nasdaq'
        self.symbols = symbols

    def get_data(self, coin, tf):
        df_ohlcv = get_data_nasdaq(self.prepath + coin + '_10y.csv', tf, filter_ts=False)
        df_ohlcv = df_ohlcv[df_ohlcv.index > pd.to_datetime(self.start_date)]
        return df_ohlcv

    def get_symbols(self):
        return self.symbols
