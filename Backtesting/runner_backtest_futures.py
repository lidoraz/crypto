from Data import CryptoData  # , NasdaqData
from Backtesting.optimize_futures import find_optimal_strategy


def override_test_one_strategy(param, params):
    # param = ('5T', 150, 3, 25, 1, 20, 1.2)
    return {k: [param[i]] for i, (k, v) in enumerate(params.items())}


def run_VOLEMA(data_wrapper, start_date, n_jobs):
    strategy = "EMAVOL"

    params = {  # 1h,9,14,15,26.0,68.0,1.9,324.30691727745153
        'tf': ['5T', '15T'],  # 'tf': ['1H', '15T'],  # ['1H', '15T'],  # ['1H'] # '15min',
        'ema_ahead': [100, 150, 180, 200],
        'n_ema_soon': [3, 7, 14],
        'ema_fast_ahead': [14, 25, 50],
        'vol_ema': [1, 10, 20],  # EMA 1 should be no volume at all
        'support_ahead': [10, 20],
        'risk_reward': [1, 1.2, 1.5]
    }
    # test only one
    # n_jobs = 1
    # param = ('15T', 150, 7, 14, 20, 1.5)
    # params = override_test_one_strategy(param)
    return find_optimal_strategy(data_wrapper, start_date, strategy=strategy, optimized_params=params, n_jobs=n_jobs)


def run_optimizer():
    # tf = '1H'#, '5T'  # 15min'
    start_date = '2022-05-01'  # 22%!!
    # start_date = '2022-07-05'
    # tf = '1T'  # 15min'
    # start_date = '2022-06-01'

    n_jobs = 8
    # n_jobs = os.cpu_count()
    data_wrapper = CryptoData.get_wrapper(live=False, start_date=start_date,
                                          only_exchange='binance')  # start_date='2022-04-25'
    params = (data_wrapper, start_date, n_jobs)
    jobs = [
        run_VOLEMA(*params),
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
