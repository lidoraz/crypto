from Data import CryptoData  # , NasdaqData
from Backtesting.optimize_futures import find_optimal_strategy


def override_test_one_strategy(param):
    # param = ('5T', 150, 3, 25, 1, 20, 1.2)
    # return {k: [param[i]] for i, (k, v) in enumerate(params.items())}
    return {k: [param[k]] for k in param}


def run_VOLEMA(data_wrapper, start_date, n_jobs):
    strategy = "EMAVOL"
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': ['1H', '15T'],  # 'tf': ['1H', '15T'],  # ['1H', '15T'],  # ['1H'] # '15min', ['5T', '15T', '1H']
        'ema_ahead': [100, 150, 200, 400],
        'n_ema_soon': [3, 7, 14],
        'ema_fast_ahead': [14, 25, 50],
        'vol_ema': [1, 10, 20],  # EMA 1 should be no volume at all
        'support_ahead': [5, 10, 20],
        'risk_reward': [1, 1.2, 1.5]
    }
    # test only one
    # param = {'tf': '15T', "ema_ahead": 200, "n_ema_soon": 3, "ema_fast_ahead": 14,
    #          "vol_ema": 20, "support_ahead": 20, "risk_reward": 1.2}
    # 1H,100,14,25,1,20,1.0
    # param = {"name": "EMAVOL", "ema_ahead": 100, "n_ema_soon": 14, "ema_fast_ahead": 25, "vol_ema": 20,
    #          "support_ahead": 5, "risk_reward": 1.0}
    # param['tf'] = '1H'
    # n_jobs = 1
    # {"ema_ahead": 200, "n_ema_soon": 3, "ema_fast_ahead": 14, "vol_ema": 20, "support_ahead": 20, "risk_reward": 1.2}
    # params = override_test_one_strategy(param)
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_EMABB(data_wrapper, start_date, n_jobs):
    strategy = "EMABB"
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': ['5T', '15T'],  # 'tf': ['1H', '15T'],  # ['1H', '15T'],  # ['1H'] # '15min',
        'ema_slow_lk': [100, 150, 200],
        'ema_fast_lk': [14, 25, 50],
        'n_bb_soon': [3, 7],
        'bb_lk': [20],
        'bb_std': [2, 2.2],
        'sl_pct': [0.005, 0.01],
        'risk_reward': [1, 1.2, 1.5]
    }
    # test only one
    n_jobs = 1
    param = {'tf': '15T', 'ema_slow_lk': 250, 'ema_fast_lk': 25, 'n_bb_soon': 3,
             'bb_lk': 20, 'bb_std': 2, 'sl_pct': 0.01, 'risk_reward': 1.1}
    params = override_test_one_strategy(param)
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_EMA3(data_wrapper, start_date, n_jobs):
    strategy = "EMA3"
    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': ['15T'],  # 'tf': ['1H', '15T'],  # ['1H', '15T'],  # ['1H'] # '15min',
        'ema_slow_lk': [100, 150, 200],
        'ema_fast_lk': [14, 25, 50],
        'n_bb_soon': [3, 7],
        'bb_lk': [20],
        'bb_std': [2, 2.2],
        'sl_pct': [0.005, 0.01],
        'risk_reward': [1, 1.2, 1.5]
    }
    # test only one
    n_jobs = 1
    param = {'tf': '15T'}
    params = override_test_one_strategy(param)
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_optimizer():
    # tf = '1H'#, '5T'  # 15min'
    start_date = '2022-02-01'  # 22%!!
    # start_date = '2022-07-05'
    # tf = '1T'  # 15min'
    # start_date = '2022-06-01'
    # TODO: need to remember that indicators dont work well from start as it needs about 200 candles to operate correctly.
    n_jobs = 8
    # n_jobs = os.cpu_count()
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date,
                                          only_exchange='binance')  # start_date='2022-04-25'
    params = (data_wrapper, start_date, n_jobs)
    jobs = [
        run_VOLEMA,
        # run_EMABB,
        # run_EMA3,
    ]
    print(f'Test result for multiple strategies: starting={start_date}')
    from Backtesting.old.optimize import TIME_CONV
    from datetime import datetime
    with open(f"Backtesting/strategy_output/{datetime.now().strftime(TIME_CONV)}_Crypto_summed_results.csv", 'w') as fp:
        for job in jobs:

            strategy, metrics = job(*params)
            metrics['profit_pct'] = f"{metrics['profit_pct']:0.2%}"
            print(strategy, metrics)
            print((strategy, metrics), file=fp)


if __name__ == '__main__':
    run_optimizer()
