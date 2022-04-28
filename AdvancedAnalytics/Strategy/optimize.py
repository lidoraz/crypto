import pandas as pd
from datetime import datetime

from AdvancedAnalytics.Strategy.DataWrap import ProviderData
from AdvancedAnalytics.Strategy.Strategies import *
from Crypto.DataProcessing.DataProvider import TIME_CONV


# ind_ahead, params,
#                  coin, tf,
#                  n_rsi_soon=10, low_rsi=30, high_rsi=70


def mark_enter_exit_points(data_class: ProviderData, strategy: str, params):
    symbols = data_class.get_symbols()
    sum_pct = 0
    trades_str = []
    open_trades = 0

    for symbol in symbols:
        df = data_class.get_data(symbol, params['tf'])
        # TODO: continue here; try to pass a stratgey with all params above.
        strategy_class = All_STRATEGIES[strategy.upper()](params)
        df = strategy_class.add_indicators(df)
        act_sum_pct, act_trades_str, is_open = strategy_class.act(df)
        act_trades_str = [f'{symbol}- {trade}' for trade in act_trades_str]  # add symbol
        sum_pct += act_sum_pct
        trades_str += act_trades_str
        open_trades += is_open

    return sum_pct, trades_str, open_trades


def find_optimal_strategy(data_class, strategy: str, optimized_params):
    print(datetime.now().strftime(TIME_CONV))
    res = []
    l_trades_str = []
    import itertools
    # https://stackoverflow.com/questions/38721847/how-to-generate-all-combination-from-values-in-dict-of-lists-in-python
    keys, values = zip(*optimized_params.items())
    permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    for params in permutations_dicts:
        sum_pct, trades_str, n_open_trades = mark_enter_exit_points(data_class, strategy, params)
        n_trades = len(trades_str)
        print(f'{params}\t\t#trades: {n_trades}\t#n_open_trades: {n_open_trades}\t sum_pct: {sum_pct:.2%}')
        # add to list for future analysis
        params['sum_pct'] = sum_pct
        params['n_trades'] = n_trades
        params['n_open_trades'] = n_open_trades
        res.append(params)
        l_trades_str.append(trades_str)
    # cols = ['tf', 'lookahead', 'set_profit_pct', 'sum_profit_pct', 'total_trades', 'n_open_trades']
    df = pd.DataFrame(res)
    df = df.sort_values('sum_pct', ascending=False)

    # get win strategy:
    win_idx = df.index[0]
    win_sum_profit_pct = df['sum_pct'].iloc[0]
    win_trades = l_trades_str[win_idx]
    print('Index:', win_idx)
    print(f'Pct profit: {win_sum_profit_pct:.2%}')
    for trade in win_trades:
        print(trade)
    print("Total trades:", len(win_trades))

    # save df
    time = datetime.now().strftime(TIME_CONV)
    name = f'{time}_{data_class.name}_RSI_BB'

    output_path = 'AdvancedAnalytics/Strategy/strategy_output/'
    full_path_summary = output_path + name + '_summary.csv'
    full_path_trades = output_path + name + '_trades.tsv'
    df.to_csv(full_path_summary)
    with open(full_path_trades, 'w') as f:
        for trade in win_trades:
            print(trade, file=f)
