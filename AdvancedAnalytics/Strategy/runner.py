from Strategies import find_optimal_BBRSI_strategy
from data_wrappers import CryptoData, NasdaqData
import numpy as np


def get_crypto():
    from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
    from Crypto.DataProcessing.data_utils import get_data_providers, prepare_data
    params = {'time_intervals': ['1H'],  # ['15Min', '1H']
              'lookaheads': range(10, 17, 2),
              'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.05)]}
    providers = get_data_providers()
    df_prices, df_agg = prepare_data(providers, START_DATA_DATE)
    data_wrapper = CryptoData(df_prices, df_agg, COINS)
    return data_wrapper, params


def get_nasdaq():
    from Nasdaq.symbols import NASDAQ_PREPATH, nasdq_100
    params = {'time_intervals': [1],  # Nasdaq Daily data
              'lookaheads': range(10, 17, 2),
              'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.02)]}
    start_date = '2019-01-01'
    symbols = nasdq_100[1:10]
    data_wrapper = NasdaqData(symbols, NASDAQ_PREPATH, start_date=start_date)
    return data_wrapper, params


if __name__ == '__main__':
    # data_wrapper, params = get_crypto()

    data_wrapper, params = get_nasdaq()

    find_optimal_BBRSI_strategy(data_wrapper, params)
