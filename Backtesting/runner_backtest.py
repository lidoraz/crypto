from Data import CryptoData  # , NasdaqData
from Backtesting.optimize import find_optimal_strategy
import os
import numpy as np
import sys
import json


def run_MACross(data_wrapper, tf, start_date, n_jobs):
    s = 'MACROSS'
    params = {
        'tf': [tf],
        'MACROSS_short': [50],
        'MACROSS_long': [100]
        # 'MACROSS_short': range(5, 26, 5),
        # 'MACROSS_long': range(50, 101, 10)
    }

    return find_optimal_strategy(data_wrapper, start_date, strategy=s, optimized_params=params, n_jobs=n_jobs)


def run_SMAStochRSI(data_wrapper, tf, start_date, n_jobs):
    s = 'RSISTO'
    params = {
        'tf': [tf],
        'rsi_ahead': [10, 14],
        'sma_ahead': [10, 14, 20],
        'support_ahead': [40, 70, 120, 200]
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy=s, optimized_params=params, n_jobs=n_jobs)


def run_BB(data_wrapper, tf, start_date, n_jobs):
    strategy = 'BB'
    # {'tf': '1H', 'BB_ind_ahead': 20, 'BB_std': 2.0, 'BB_stop_lookahead': 70,
    # 'total_balance': 338.338, 'n_trades': 0, 'n_open_trades': 28}
    params = {
        'tf': [tf],
        'ind_ahead': [20],
        'std': [2.0],
        'stop_lookahead': [70, 120, 150]
        # 'tf': ['1H'],
        # 'BB_ind_ahead': range(10, 22, 4),
        # 'BB_std': [1.8, 2, 2.5],
        # 'BB_stop_lookahead': range(30, 401, 50)
        # 'BB_win_pct': np.linspace(0.1, 0.5, 5),  # np.linspace(0, 0.5, 5),  # range(10)
        # 'BB_lose_pct': np.linspace(0.1, 0.5, 5)  #
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


# # from testing it seems that under 1H granularity it can't generate profit.
# sell_pct is not good for RSIBB, really need to keep it on 0.
def run_RSIBB(data_wrapper, tf, start_date, n_jobs):
    strategy = 'RSIBB'
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': ['1H', '15T'], # [tf],  # ['1H', '15T'] # '15min',
        'aggressive': [False, True],  # True,
        'n_rsi_soon': [4, 7],
        'rsi_ahead': [7, 14],
        'bb_ahead': [15, 20],
        'rsi_low': [30],
        'rsi_high': [70],
        'bb_std': [2.1, 2.5, 3]

    }
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_SMAMACD(data_wrapper, tf, start_date, n_jobs):
    strategy = "SMAMACD"
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': [tf],  # ['1H'] # '15min',
        'RSIBB_aggressive': [False, True],  # True,
        'RSIBB_n_rsi_soon': [4, 7],
        'RSIBB_rsi_ahead': [14, 7],
        'RSIBB_bb_ahead': [15, 20],
        'RSIBB_rsi_low': [30],
        'RSIBB_rsi_high': [70],
        'RSIBB_bb_std': [2.1, 2.5, 3]
        # # 'tf': ['15min'],  # ['1H'] # '15min',
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_optimizer():
    tf = '1H'  # 15min'
    start_date = '2022-06-01'
    # tf = '1T'  # 15min'
    # start_date = '2022-06-01'

    n_jobs = 8
    # n_jobs = os.cpu_count()
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date,
                                          only_exchange='binance')  # start_date='2022-04-25'
    params = (data_wrapper, tf, start_date, n_jobs)
    jobs = [
        # run_HIGHCHANGE(*params),
        # TODO: add highchange as test of strategy, issue is this: in order to optimize this,
        #  it must be a duration of about 5 minutes, after that we sell if we have profit., currently sell work opposite to buy
        # run_MACross(*params),
        run_RSIBB(*params),
        # run_BB(*params),
        # run_SMAStochRSI(*params),
        # run_SMAMACD(*params)
    ]
    print(f'Test result for multiple strategies: starting={start_date}')
    from optimize import TIME_CONV
    from datetime import datetime
    with open(f"Backtesting/strategy_output/{datetime.now().strftime(TIME_CONV)}_Crypto_summed_results.csv", 'w') as fp:
        for job in jobs:
            strategy, metrics = job
            metrics['profit_pct'] = f"{metrics['profit_pct']:0.2%}"
            print(strategy, metrics)
            print((strategy, metrics), file=fp)


if __name__ == '__main__':
    run_optimizer()
