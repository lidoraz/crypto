from DataWrap import CryptoData, NasdaqData
from Strategies import find_optimal_BBRSI_strategy
import numpy as np

if __name__ == '__main__':
    # params = {'time_intervals': ['1H'],  # ['15Min', '1H']
    #           'lookaheads': range(10, 17, 2),
    #           'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.05)]}
    # data_wrapper = CryptoData.get_crypto_wrapper()

    params = {'time_intervals': [1],  # Nasdaq Daily data
              'lookaheads': range(10, 17, 2),
              'profit_percents': [round(x, 2) for x in np.arange(0.03, 0.15, 0.02)]}
    data_wrapper = NasdaqData.get_nasdaq_wrapper()

    find_optimal_BBRSI_strategy(data_wrapper, params)
