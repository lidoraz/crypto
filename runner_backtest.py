from Data import CryptoData  # , NasdaqData
from Backtesting.optimize import find_optimal_strategy
import os
import numpy as np
import sys
import json


def run_MACross(data_wrapper, start_date, n_jobs):
    params = {
        'tf': ['1H'],
        'MACROSS_short': range(5, 26, 5),
        'MACROSS_long': range(50, 101, 10)}
    find_optimal_strategy(data_wrapper, start_date, strategy='MACROSS', optimized_params=params, n_jobs=n_jobs)


def run_BB(data_wrapper, start_date, n_jobs):
    params = {
        'tf': ['1H'],
        'BB_ind_ahead': range(10, 22, 4),
        'BB_std': [1.8, 2, 2.5],
        'BB_stop_lookahead': range(30, 401, 50)
        # 'BB_win_pct': np.linspace(0.1, 0.5, 5),  # np.linspace(0, 0.5, 5),  # range(10)
        # 'BB_lose_pct': np.linspace(0.1, 0.5, 5)  #
    }
    find_optimal_strategy(data_wrapper, start_date, strategy='BB', optimized_params=params, n_jobs=n_jobs)


# # from testing it seems that under 1H granularity it can't generate profit.
# sell_pct is not good for RSIBB, really need to keep it on 0.
def run_RSIBB(start_date, data_wrapper, n_jobs):
    params = {
        'tf': ['15T', '1h'],  # ['1H'] # '15min',
        'RSIBB_n_rsi_soon': np.linspace(3, 14, 3),
        'RSIBB_rsi_ahead': np.linspace(10, 17, 3),
        'RSIBB_bb_ahead': np.linspace(10, 30, 3),
        'RSIBB_rsi_low': np.linspace(24, 34, 3),
        'RSIBB_rsi_high': np.linspace(66, 76, 3),
        'RSIBB_bb_std': [1.9, 2.1, 2.5]
    }
    # convert to int.
    for key, vals in params.items():
        if key.startswith('RSIBB'):
            params[key] = [int(x) for x in vals]
    find_optimal_strategy(data_wrapper, start_date, strategy='RSIBB', optimized_params=params, n_jobs=n_jobs)


def run_optimizer():
    # args = sys.argv[1:]
    # data = json.loads(args)
    # start_date = data['start_date']
    # mp = data['mp']
    # strategy_str = data['strategy']
    # data.pop('start_date')
    # data.pop('mp')
    start_date = '2022-05-01'
    strategy = 'RSIBB'

    n_jobs = os.cpu_count()
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date,
                                          only_exchange='binance')  # start_date='2022-04-25'
    strategy = strategy.upper()
    if strategy == 'RSIBB':
        run_RSIBB(start_date, data_wrapper, n_jobs)
    elif strategy == 'BB':
        run_BB(start_date, data_wrapper, n_jobs)
    elif strategy == 'MACROSS':
        run_MACross(start_date, data_wrapper, n_jobs)
    else:
        raise ValueError()


if __name__ == '__main__':
    run_optimizer()
