from Strategies import find_optimal_BBRSI_strategy
from data_wrappers import CryptoData, NasdaqData
import numpy as np


def run_crypto():
    from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
    from Crypto.DataProcessing.data_utils import get_data_providers, prepare_data
    params = {'time_intervals': ['15Min', '1H'],
              'lookaheads': range(10, 17, 2),
              'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.02)]}
    providers = get_data_providers()
    df_prices, df_agg = prepare_data(providers, START_DATA_DATE)
    data_class = CryptoData(df_prices, COINS)
    find_optimal_BBRSI_strategy(data_class, params)


def run_nasdaq():
    from Nasdaq.symbols import NASDAQ_PREPATH, nasdq_100
    params = {'time_intervals': [1],  # Nasdaq Daily data
              'lookaheads': range(10, 17, 2),
              'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.02)]}
    start_date = '2019-01-01'
    symbols = nasdq_100[1:10]
    data = NasdaqData(symbols, NASDAQ_PREPATH, start_date=start_date)
    find_optimal_BBRSI_strategy(data, params)


if __name__ == '__main__':
    # run_crypto()

    run_nasdaq()
