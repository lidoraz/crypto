from .ProviderData import ProviderData
from Indicators import CandleStick


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

    @staticmethod
    def get_crypto_wrapper():
        from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
        from Crypto.DataProcessing.data_utils import get_data_providers, prepare_data
        providers = get_data_providers()
        df_prices, df_agg = prepare_data(providers, START_DATA_DATE)
        data_wrapper = CryptoData(df_prices, df_agg, COINS)
        return data_wrapper
