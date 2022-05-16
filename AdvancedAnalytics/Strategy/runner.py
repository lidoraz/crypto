from DataWrap import CryptoData, NasdaqData
from optimize import find_optimal_strategy
import numpy as np

# params = {'time_intervals': ['1D'],  # Nasdaq Daily data
#           'lookaheads': range(6, 17, 2),
#           'profit_percents': np.arange(0, 0.15, 0.02)}
# data_wrapper = NasdaqData.get_wrapper(start_date='2016-01-01')

if __name__ == '__main__':
    # DS ################################################################################################################################################
    # TODO: in optimizer filter out params that are not being used. can extract this with a list from each strategy
    optimize_params = {'tf': ['1H', '4H'],  # ['15Min', '1H']
                       'sell_pct': np.arange(0, 0.10, 0.02)}  # 0.15 is too much # not a good  paramter.
    # check more for 5min and 15min, and if there is a difference between 15 days trading to 1.5 month of trading

    start_date = '2022-03-01'
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date)  # start_date='2022-04-25'

    print('START_DATE = ', start_date)


    # n_jobs = 1

    # optimize_params = {'tf': ['1D'],  # Nasdaq Daily data
    #           'set_profit_pct': np.arange(0, 0.15, 0.02)}
    # data_wrapper = NasdaqData.get_wrapper(start_date='2021-06-01')

    # Strategies ########################################################################################################################################
    def run_MACross():
        strategy_params_macross = {'MACROSS_short': range(5, 26, 5),
                                   'MACROSS_long': range(50, 101, 10)}
        optimize_params.update(strategy_params_macross)
        find_optimal_strategy(data_wrapper, strategy='MACROSS', optimized_params=optimize_params)

    # # from testing it seems that under 1H granularity it can't generate profit.
    # sell_pct is not good for RSIBB, really need to keep it on 0.
    def run_RSIBB():
        strategy_params_rsi = {
            'tf': ['1H'],  # ['1H'] # '15min',
            'sell_pct': [0],
            'RSIBB_n_rsi_soon': np.linspace(3, 14, 6),
            'RSIBB_rsi_ahead': np.linspace(10, 17, 6),
            'RSIBB_bb_ahead': np.linspace(10, 30, 6),
            'RSIBB_rsi_low': [30],
            'RSIBB_rsi_high': [70],
            'RSIBB_bb_std': [2]
            # 'RSIBB_n_rsi_soon': range(5, 14, 2),
            # 'RSIBB_rsi_ahead': range(10, 17, 2),
            # 'RSIBB_bb_ahead': range(10, 30, 2),
            # 'RSIBB_rsi_low': range(22, 36, 2),
            # 'RSIBB_rsi_high': range(66, 78, 2),
            # 'RSIBB_bb_std': np.linspace(1.8, 3, 6)
        }
        # convert to int.
        for key, vals in strategy_params_rsi.items():
            if key.startswith('RSIBB'):
                strategy_params_rsi[key] = [int(x) for x in vals]
        find_optimal_strategy(data_wrapper, strategy='RSIBB', optimized_params=strategy_params_rsi)


    def run_BB():
        # BB #############
        # strategy_params_rsi = {'BB_ind_ahead': range(10, 22, 4),
        #                        'BB_std': [2, 2.5],
        #                        'BB_STOP_lookaheads_index': range(10),
        #                        }
        strategy_params_rsi = {
            'tf': ['1H'],
            'sell_pct': [0],
            'BB_ind_ahead': range(10, 22, 4),
            'BB_std': [1.8, 2, 2.5],
            'BB_stop_lookahead': range(30, 401, 50)
            # 'BB_win_pct': np.linspace(0.1, 0.5, 5),  # np.linspace(0, 0.5, 5),  # range(10)
            # 'BB_lose_pct': np.linspace(0.1, 0.5, 5)  #
        }
        optimize_params.update(strategy_params_rsi)
        n_jobs = 8
        find_optimal_strategy(data_wrapper, strategy='BB', optimized_params=optimize_params, n_jobs=n_jobs)


    run_RSIBB()
    # run_BB()
