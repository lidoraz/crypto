from DataWrap import CryptoData, NasdaqData
from Strategies import find_optimal_BBRSI_strategy
import numpy as np

if __name__ == '__main__':
    params = {'time_intervals': ['1H'],  # ['15Min', '1H']
              'lookaheads': range(10, 17, 2),
              'profit_percents': np.arange(0, 0.15, 0.02)}
    print(params['profit_percents'])
    data_wrapper = CryptoData.get_wrapper()

    # params = {'time_intervals': ['1D'],  # Nasdaq Daily data
    #           'lookaheads': range(6, 17, 2),
    #           'profit_percents': np.arange(0, 0.15, 0.02)}
    # data_wrapper = NasdaqData.get_wrapper(start_date='2016-01-01')

    find_optimal_BBRSI_strategy(data_wrapper, params)
