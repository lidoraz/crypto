from Data import CryptoData  # , NasdaqData
from optimize import find_optimal_strategy
import numpy as np


def run_MACross():
    optimize_params = {'tf': ['1H', '4H'],  # ['15Min', '1H']
                       'sell_pct': np.arange(0, 0.10, 0.02)}  # 0.15 is too much # not a good  paramter.
    strategy_params_macross = {'MACROSS_short': range(5, 26, 5),
                               'MACROSS_long': range(50, 101, 10)}
    optimize_params.update(strategy_params_macross)
    find_optimal_strategy(data_wrapper, strategy='MACROSS', optimized_params=optimize_params)


def run_BB():
    optimize_params = {'tf': ['1H', '4H'],  # ['15Min', '1H']
                       'sell_pct': np.arange(0, 0.10, 0.02)}  # 0.15 is too much # not a good  paramter.
    strategy_params_bb = {
        'tf': ['1H'],
        'sell_pct': [0],
        'BB_ind_ahead': range(10, 22, 4),
        'BB_std': [1.8, 2, 2.5],
        'BB_stop_lookahead': range(30, 401, 50)
        # 'BB_win_pct': np.linspace(0.1, 0.5, 5),  # np.linspace(0, 0.5, 5),  # range(10)
        # 'BB_lose_pct': np.linspace(0.1, 0.5, 5)  #
    }
    n_jobs = 8
    find_optimal_strategy(data_wrapper, strategy='BB', optimized_params=strategy_params_bb, n_jobs=n_jobs)


# # from testing it seems that under 1H granularity it can't generate profit.
# sell_pct is not good for RSIBB, really need to keep it on 0.
def run_RSIBB():
    strategy_params_rsi = {
        'tf': ['1H'],  # ['1H'] # '15min',
        'sell_pct': [0],
        'RSIBB_n_rsi_soon': np.linspace(3, 14, 3),
        'RSIBB_rsi_ahead': np.linspace(10, 17, 3),
        'RSIBB_bb_ahead': np.linspace(10, 30, 3),
        'RSIBB_rsi_low': [30],
        'RSIBB_rsi_high': [70],
        'RSIBB_bb_std': [2]
    }
    # convert to int.
    for key, vals in strategy_params_rsi.items():
        if key.startswith('RSIBB'):
            strategy_params_rsi[key] = [int(x) for x in vals]
    find_optimal_strategy(data_wrapper, strategy='RSIBB', optimized_params=strategy_params_rsi)


# 'RSIBB_n_rsi_soon': range(5, 14, 2),
# 'RSIBB_rsi_ahead': range(10, 17, 2),
# 'RSIBB_bb_ahead': range(10, 30, 2),
# 'RSIBB_rsi_low': range(22, 36, 2),
# 'RSIBB_rsi_high': range(66, 78, 2),
# 'RSIBB_bb_std': np.linspace(1.8, 3, 6)

if __name__ == '__main__':
    # DS ################################################################################################################################################
    # TODO: in optimizer filter out params that are not being used. can extract this with a list from each strategy
    # optimize_params = {'tf': ['1H', '4H'],  # ['15Min', '1H']
    #                    'sell_pct': np.arange(0, 0.10, 0.02)}  # 0.15 is too much # not a good  paramter.
    # check more for 5min and 15min, and if there is a difference between 15 days trading to 1.5 month of trading

    start_date = '2022-05-11'
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date)  # start_date='2022-04-25'

    print('START_DATE = ', start_date)
    run_RSIBB()
    # run_BB()
