from Data import CryptoData  # , NasdaqData
from Backtesting.optimize import find_optimal_strategy
import os
import numpy as np
import sys
import json


def run_MACross(data_wrapper, tf, start_date, n_jobs):
    params = {
        'tf': [tf],
        'MACROSS_short': [50],
        'MACROSS_long': [100]
        # 'MACROSS_short': range(5, 26, 5),
        # 'MACROSS_long': range(50, 101, 10)
    }

    return find_optimal_strategy(data_wrapper, start_date, strategy='MACROSS', optimized_params=params, n_jobs=n_jobs)


def run_SMAStochRSI(data_wrapper, tf, start_date, n_jobs):
    params = {
        'tf': [tf],
        'RSISTO_rsi_ahead': [10, 14],
        'RSISTO_sma_ahead': [10, 14, 20],
        'RSISTO_support_ahead': [40, 70, 120, 200]
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy='RSISTO', optimized_params=params, n_jobs=n_jobs)


def run_BB(data_wrapper, tf, start_date, n_jobs):
    # {'tf': '1H', 'BB_ind_ahead': 20, 'BB_std': 2.0, 'BB_stop_lookahead': 70,
    # 'total_balance': 338.338, 'n_trades': 0, 'n_open_trades': 28}
    params = {
        'tf': [tf],
        'BB_ind_ahead': [20],
        'BB_std': [2.0],
        'BB_stop_lookahead': [70, 120, 150]
        # 'tf': ['1H'],
        # 'BB_ind_ahead': range(10, 22, 4),
        # 'BB_std': [1.8, 2, 2.5],
        # 'BB_stop_lookahead': range(30, 401, 50)
        # 'BB_win_pct': np.linspace(0.1, 0.5, 5),  # np.linspace(0, 0.5, 5),  # range(10)
        # 'BB_lose_pct': np.linspace(0.1, 0.5, 5)  #
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy='BB', optimized_params=params, n_jobs=n_jobs)


# # from testing it seems that under 1H granularity it can't generate profit.
# sell_pct is not good for RSIBB, really need to keep it on 0.
def run_RSIBB(data_wrapper, tf, start_date, n_jobs):
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': [tf],  # ['1H'] # '15min',
        'RSIBB_aggressive': [False, True],  # True,
        'RSIBB_n_rsi_soon': [4, 7],
        'RSIBB_rsi_ahead': [14, 7],
        'RSIBB_bb_ahead': [15, 20],
        'RSIBB_rsi_low': [30],
        'RSIBB_rsi_high': [70],
        'RSIBB_bb_std': [2.1, 2.5, 3]
        # 'tf': ['15min'],  # ['1H'] # '15min',
        # 'RSIBB_aggressive': [False],  # True,
        # 'RSIBB_n_rsi_soon': [5, 9],
        # 'RSIBB_rsi_ahead': [10, 14],
        # 'RSIBB_bb_ahead': [15, 20],
        # 'RSIBB_rsi_low': [28, 30, 32],
        # 'RSIBB_rsi_high': [68, 70, 72],
        # 'RSIBB_bb_std': [2.0, 2.5]
        # 'tf': ['1h'],  # ['1H'] # '15min',
        # 'RSIBB_n_rsi_soon': [int(x) for x in np.linspace(5, 14, 3)],
        # 'RSIBB_rsi_ahead': [int(x) for x in np.linspace(5, 17, 6)],
        # 'RSIBB_bb_ahead': [int(x) for x in np.linspace(10, 20, 3)],
        # 'RSIBB_rsi_low': np.linspace(26, 32, 3),
        # 'RSIBB_rsi_high': np.linspace(68, 74, 3),
        # 'RSIBB_bb_std': [1.9, 2.1, 2.5]
    }
    return find_optimal_strategy(data_wrapper, start_date, strategy='RSIBB', optimized_params=params, n_jobs=n_jobs)


def run_optimizer():
    # args = sys.argv[1:]
    # data = json.loads(args)
    # start_date = data['start_date']
    # mp = data['mp']
    # strategy_str = data['strategy']
    # data.pop('start_date')
    # data.pop('mp')
    tf = '1H'  # 15min'
    start_date = '2022-03-01'

    n_jobs = 8  # os.cpu_count()
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date,
                                          only_exchange='binance')  # start_date='2022-04-25'
    # [268.067, 174.936, 210.714]
    jobs = [
        # run_MACross(data_wrapper, tf, start_date, n_jobs),
        run_RSIBB(data_wrapper, tf, start_date, n_jobs),
        run_BB(data_wrapper, tf, start_date, n_jobs),
        run_SMAStochRSI(data_wrapper, tf, start_date, n_jobs)
    ]
    print(f'Test result for multiple strategies: starting={start_date}')
    for job in jobs:
        strategy, metrics = job
        metrics['profit_pct'] = f"{metrics['profit_pct']:0.2%}"
        print(strategy, metrics)

    # strategy = strategy.upper()
    # if strategy == 'RSIBB':
    #     run_RSIBB(data_wrapper, start_date, n_jobs)
    # elif strategy == 'BB':
    #     run_BB(data_wrapper, start_date, n_jobs)
    # elif strategy == 'MACROSS':
    #     run_MACross(data_wrapper, start_date, n_jobs)
    # else:
    #     raise ValueError()


if __name__ == '__main__':
    run_optimizer()
