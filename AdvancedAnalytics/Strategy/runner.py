from AdvancedAnalytics.Strategy.DataWrap.CryptoData import CryptoDataLive
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
    optimize_params = {'tf': ['1H'],  # ['15Min', '1H']
                       'sell_pct': np.arange(0, 0.10, 0.02)}  # 0.15 is too much
    data_wrapper = CryptoDataLive.get_wrapper(update_sec_every=120, is_safe=False,
                                              start_date='2022-04-26')  # start_date='2022-04-25'

    # optimize_params = {'tf': ['1D'],  # Nasdaq Daily data
    #           'set_profit_pct': np.arange(0, 0.15, 0.02)}
    # data_wrapper = NasdaqData.get_wrapper(start_date='2021-06-01')

    # Strategies ########################################################################################################################################

    # MACross ###################################################################################################
    strategy_params_macross = {'MACROSS_short': range(5, 26, 5),
                               'MACROSS_long': range(50, 101, 10)}
    optimize_params.update(strategy_params_macross)
    find_optimal_strategy(data_wrapper, strategy='MACROSS', optimized_params=optimize_params)
    # RSIBB ###################################################################################################
    strategy_params_rsi = {'RSIBB_n_rsi_soon': range(5, 14, 2),
                           'RSIBB_ind_ahead': range(10, 17, 2),
                           'RSIBB_BB_std': [1.8, 2, 2.5, 3]}
    # from testing it seems that under 1H granularity it can't generate profit.
    optimize_params.update(strategy_params_rsi)
    find_optimal_strategy(data_wrapper, strategy='RSIBB', optimized_params=optimize_params)

    # BB #############
    strategy_params_rsi = {'BB_ind_ahead': range(5, 18, 4),
                           'BB_std': [1.5, 2, 2.5]
                           }
    optimize_params.update(strategy_params_rsi)
    find_optimal_strategy(data_wrapper, strategy='BB', optimized_params=optimize_params)
