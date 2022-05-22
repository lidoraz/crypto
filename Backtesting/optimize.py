import pandas as pd
import itertools
from datetime import datetime
from tqdm import tqdm
from joblib import Parallel, delayed
import os

from Data import ProviderData
from Backtesting.Strategies import *



def run_strategy(df, stragey: Strategy, trade_comission=0.001):
    sum_pct_net = 0
    buy_idx_vars = None
    trades_str = []
    buy_ts = None
    for curr_ts, row in df.iterrows():
        if not buy_ts:
            buy_vars = stragey.act_buy(curr_ts, row)
            if buy_vars:
                buy_ts = buy_vars['buy_idx']
                buy_idx_vars = buy_vars
        else:
            sell_ts = curr_ts
            buy_price = buy_idx_vars['buy_price']
            sell_price_win_stop = buy_idx_vars['sell_price_win_stop']
            sell_price_lose_stop = buy_idx_vars['sell_price_lose_stop']
            sell_price = df['close'].loc[sell_ts]
            hours_holding = int((sell_ts - buy_ts).total_seconds() // 3600)
            if sell_price > sell_price_win_stop:
                sold_cause = 'WIN_STOP'
                sold_price = sell_price_win_stop
            elif sell_price < sell_price_lose_stop:
                sold_cause = 'LOSE_STOP'
                sold_price = sell_price_lose_stop
            elif row['SELL_ALGO']:
                sold_cause = 'ALGO_SELL'
                sold_price = sell_price
            else:
                continue
            profit_pct = (sold_price / buy_price) - 1
            profit_pct_net = profit_pct - (trade_comission * 2)  # plus commission
            trade_arr = [sold_cause, buy_ts, round(buy_price, 2),
                         sell_ts, round(sold_price, 2), hours_holding, f'{profit_pct_net:.2%}']
            trade_arr = list(map(str, trade_arr))
            transaction = 'Trade:' + "\t".join(trade_arr)
            trades_str.append(transaction)
            sum_pct_net += profit_pct_net
            buy_ts = None
    is_trade_open = buy_ts is not None
    return sum_pct_net, trades_str, is_trade_open


def mark_enter_exit_points(provider: ProviderData, strategy: str, params):
    symbols = provider.get_symbols()
    sum_pct = 0
    trades_str = []
    n_open_trades = 0
    tf = params['tf']
    for symbol in symbols:
        df = provider.get_data(symbol, tf)
        strategy_class = All_STRATEGIES[strategy.upper()](params)
        df = strategy_class.add_indicators(df)
        act_sum_pct, act_trades_str, is_open = run_strategy(df, strategy_class, trade_comission=0.001)
        act_trades_str = [f'{symbol}- {trade}' for trade in act_trades_str]  # add symbol
        sum_pct += act_sum_pct
        trades_str += act_trades_str
        n_open_trades += is_open

    n_trades = len(trades_str)
    print(f'{params}\t\t#trades: {n_trades}\t#n_open_trades: {n_open_trades}\t sum_pct: {sum_pct:.2%}')
    return sum_pct, trades_str, n_open_trades


def find_optimal_strategy(provider: ProviderData, start_date, strategy: str, optimized_params: dict, n_jobs=8):
    time_start = datetime.now()
    # filter out not relevant params:
    keys_to_remove = [k for k in optimized_params if not k.startswith(strategy) and k not in ['tf', 'sell_pct']]
    optimized_params = {k: optimized_params[k] for k in optimized_params if k not in keys_to_remove}
    print(f'Finding optimal strategies with these params:', optimized_params.keys())
    # iterate permutation with dicts: https://stackoverflow.com/questions/38721847/how-to-generate-all-combination-from-values-in-dict-of-lists-in-python
    keys, values = zip(*optimized_params.items())
    permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    # TODO: Preloaded is needed for the multiprocessing to avoid multiple access for DB, try how to solve this
    provider_loaded = provider.get_offline_wrapper(tfs=optimized_params['tf'])
    print('Running with n_jobs:', n_jobs)
    if n_jobs == 1:
        print('Debug Mode..')
        job_results = []
        for params in tqdm(permutations_dicts):
            job_results.append(mark_enter_exit_points(provider_loaded, strategy, params))
    else:
        job_results = Parallel(n_jobs=n_jobs)(
            delayed(mark_enter_exit_points)(provider_loaded, strategy, params) for params in tqdm(permutations_dicts))

    l_trades_str = []
    res = []
    for params, job_result in zip(permutations_dicts, job_results):
        sum_pct, trades_str, n_open_trades = job_result
        params['sum_pct'] = sum_pct
        params['n_trades'] = len(trades_str)
        params['n_open_trades'] = n_open_trades
        l_trades_str.append(trades_str)
        res.append(params)

    df = pd.DataFrame(res)
    df = df.sort_values('sum_pct', ascending=False)

    # get win strategy:
    win_idx = df.index[0]
    win_sum_profit_pct = df['sum_pct'].iloc[0]
    win_trades = l_trades_str[win_idx]
    print('Index:', win_idx)
    print('Params:', df.iloc[0].to_dict())
    print(f'Pct profit: {win_sum_profit_pct:.2%}')
    for trade in win_trades:
        print(trade)
    print("Total trades:", len(win_trades))

    # save df
    time = datetime.now()
    print(f"TIME TOOK: {int((time - time_start).total_seconds() / 60)} min")
    TIME_CONV = "%y%m%dT%H%M%S"
    name = f'{time.strftime(TIME_CONV)}_{start_date}_{provider.name}_{strategy}'

    output_path = 'Backtesting/strategy_output/'
    os.makedirs(output_path, exist_ok=True)

    full_path_summary = output_path + name + '_summary.csv'
    full_path_trades = output_path + name + '_trades.tsv'
    df.to_csv(full_path_summary)
    with open(full_path_trades, 'w') as f:
        for trade in win_trades:
            print(trade, file=f)
