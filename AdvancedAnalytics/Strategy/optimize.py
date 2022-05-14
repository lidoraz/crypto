import pandas as pd
import itertools
from datetime import datetime
from tqdm import tqdm
from joblib import Parallel, delayed

from AdvancedAnalytics.Strategy.DataWrap import ProviderData
from AdvancedAnalytics.Strategy.Strategies import *

TIME_CONV = "%Y-%m-%dT%H:%M:%S"


# TODO: Strategy: A better way to test stratgies is to compare each day the market, and look whenever there is a new oppertunity.
#  Selecting the best oppertunity should be chosen if wanted (maybe lowest RSI)
#  Next, maybe compare with a budget, and buying a trade with comparing other opportunities.

# it looks like lookahead of less than 5 is very volatile, need to restrict number of transactions
# Some coins do not change as frequent like GCOIN, so it is harder to count on the performance on these coins.
# 15Min trade made the highest value, but number of trades was very high as well and cannot be guaranteed.


def run_strategy(df, stragey: Strategy, sell_pct, trade_comission=0.001):
    sum_pct_net = 0
    buy_idx_vars = None
    trades_str = []
    buy_idx = None
    for idx, row in df.iterrows():
        if not buy_idx:
            buy_vars = stragey.act_buy(idx, row)
            if buy_vars:
                buy_idx = buy_vars['buy_idx']
                buy_idx_vars = buy_vars
        else:
            sell_idx = idx
            buy_price = buy_idx_vars['buy_price']
            sell_price_win_stop = buy_idx_vars['sell_price_win_stop']
            sell_price_lose_stop = buy_idx_vars['sell_price_lose_stop']
            sell_price = df['close'].loc[sell_idx]
            hours_holding = (sell_idx - buy_idx).total_seconds() // 3600
            profit_pct = (sell_price / buy_price) - 1
            profit_pct_net = profit_pct - (trade_comission * 2)  # plus commission
            if sell_pct == 0 or (abs(profit_pct_net) > sell_pct > 0):
                if sell_price > sell_price_win_stop:
                    sell_cause = 'WIN_STOP'
                elif sell_price < sell_price_lose_stop:
                    sell_cause = 'LOSE_STOP'
                elif row['SELL_ALGO']:
                    sell_cause = 'ALGO_SELL'
                else:
                    continue
                trade_arr = [sell_cause, buy_idx, round(buy_price, 2),
                             sell_idx, round(sell_price, 2), hours_holding, f'{profit_pct_net:.2%}']
                trade_arr = list(map(str, trade_arr))
                transaction = 'Trade:' + "\t".join(trade_arr)
                trades_str.append(transaction)
                sum_pct_net += profit_pct_net
                buy_idx = None
    is_trade_open = buy_idx is not None
    return sum_pct_net, trades_str, is_trade_open


def mark_enter_exit_points(provider: ProviderData, strategy: str, params):
    symbols = provider.get_symbols()
    sum_pct = 0
    trades_str = []
    n_open_trades = 0
    tf = params['tf']
    sell_pct = params['sell_pct']
    for symbol in symbols:
        df = provider.get_data(symbol, tf)
        # print(symbol)
        # if symbol == 'GCOIN':
        #     print()
        strategy_class = All_STRATEGIES[strategy.upper()](params)
        df = strategy_class.add_indicators(df)
        # df = df.dropna() # TODO: Test this
        act_sum_pct, act_trades_str, is_open = run_strategy(df, strategy_class,
                                                            sell_pct=sell_pct, trade_comission=0.001)
        act_trades_str = [f'{symbol}- {trade}' for trade in act_trades_str]  # add symbol
        sum_pct += act_sum_pct
        trades_str += act_trades_str
        n_open_trades += is_open

    n_trades = len(trades_str)
    print(f'{params}\t\t#trades: {n_trades}\t#n_open_trades: {n_open_trades}\t sum_pct: {sum_pct:.2%}')
    return sum_pct, trades_str, n_open_trades


def find_optimal_strategy(provider: ProviderData, strategy: str, optimized_params: dict, n_jobs=8):
    time_start = datetime.now()
    print()
    res = []
    l_trades_str = []
    # filter out not relevant params:
    keys_to_remove = [k for k in optimized_params if not k.startswith(strategy) and k not in ['tf', 'sell_pct']]
    optimized_params = {k: optimized_params[k] for k in optimized_params if k not in keys_to_remove}
    print(f'Finding optimal strategies with these params:', optimized_params.keys())
    # iterate permutation with dicts: https://stackoverflow.com/questions/38721847/how-to-generate-all-combination-from-values-in-dict-of-lists-in-python
    keys, values = zip(*optimized_params.items())
    permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    # TODO: Preloaded is needed for the multiprocessing to avoid multiple access for DB, try how to solve this
    provider_loaded = provider.get_preloaded(optimized_params['tf'])
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
    name = f'{time.strftime(TIME_CONV)}_{provider.name}_{strategy}'

    output_path = 'AdvancedAnalytics/Strategy/strategy_output/'
    full_path_summary = output_path + name + '_summary.csv'
    full_path_trades = output_path + name + '_trades.tsv'
    df.to_csv(full_path_summary)
    with open(full_path_trades, 'w') as f:
        for trade in win_trades:
            print(trade, file=f)
