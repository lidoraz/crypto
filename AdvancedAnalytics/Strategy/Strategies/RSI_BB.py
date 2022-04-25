from Indicators import RSI, BollingerBands, SMA
import pandas as pd
from datetime import datetime
from Crypto.DataProcessing.DataProvider import TIME_CONV
from . import mark_enter_exit_points


# TODO: Strategy: A better way to test stratgies is to compare each day the market, and look whenever there is a new oppertunity.
#  Selecting the best oppertunity should be chosen if wanted (maybe lowest RSI)
#  Next, maybe compare with a budget, and buying a trade with comparing other opportunities.

# it looks like lookahead of less than 5 is very volatile, need to restrict number of transactions
## Some coins do not change as frequent like GCOIN, so it is harder to count on the performance on these coins.
## 15Min trade made the highest value, but number of trades was very high as well and cannot be guaranteed.


def add_indicators(df, ind_ahead, n_rsi_soon=10, low_rsi=30, high_rsi=70):
    # n_rsi_soon: when RSI has alert, how forward to notify that alert
    ind_rsi = RSI(ind_ahead)
    ind_bb = BollingerBands(ind_ahead)
    ind_sma = SMA(100)
    df = df.join(ind_rsi.calc(df))
    df = df.join(ind_bb.calc(df))
    df = df.join(ind_sma.calc(df))
    df = df.dropna()

    rsi_col = f"RSI_{ind_ahead}"
    df['RSI_70'] = df[rsi_col] > high_rsi  # has passed RSI 70
    df['RSI_30'] = df[rsi_col] < low_rsi  # has passed RSI 30
    df['OVER_BB'] = df[f'BBTOP_{ind_ahead}'] < df['close']
    df['BELOW_BB'] = df[f'BBBOT_{ind_ahead}'] > df['close']

    # buy condition
    df[f'RSI_BELOW_30_ROWS{n_rsi_soon}'] = df['RSI_30'].rolling(n_rsi_soon).sum() > 0
    df['OVER_MID_BB'] = df['close'] > df[f'SMA_{ind_ahead}']

    # sell condition
    df[f'RSI_OVER_70_ROWS{n_rsi_soon}'] = df['RSI_70'].rolling(n_rsi_soon).sum() > 0
    df[f'BELOW_MID_BB'] = df['close'] < df[f'SMA_{ind_ahead}']

    df['BUY_ALGO_BBRSI'] = df[f'RSI_BELOW_30_ROWS{n_rsi_soon}'] & df['OVER_MID_BB']
    df['SELL_ALGO_BBRSI'] = df[f'RSI_OVER_70_ROWS{n_rsi_soon}'] & df['BELOW_MID_BB']

    # # add stop-loss
    # # Handled during the DF iter rows
    # df['SELL_WIN_STOP'] = df[f'BBTOP_{ind_ahead}'] < df['close']
    # df['SELL_LOSE_STOP'] = df[f'BBBOT_{ind_ahead}'] > df['close']
    return df


def find_optimal_BBRSI_strategy(data_class, params):
    print(datetime.now().strftime(TIME_CONV))
    # filter_datetime = adjust_plot_start_datetime(tf)

    time_intervals = params['time_intervals']
    lookaheads = params['lookaheads']
    profit_pcts = params['profit_percents']

    res = []
    l_trades = []
    l_trades_str = []
    for tf in time_intervals:
        for lookahead in lookaheads:
            for set_profit_pct in profit_pcts:
                run_params = {'tf': tf,
                              'lookahead': lookahead,
                              'set_profit_pct': set_profit_pct,
                              'n_rsi_soon': 3}
                sum_pct, trades, trades_str, n_open_trades = mark_enter_exit_points(data_class, add_indicators,
                                                                                    run_params)
                res.append([tf, lookahead, set_profit_pct, sum_pct, len(trades_str), n_open_trades])
                l_trades.append(trades)
                l_trades_str.append(trades_str)
    cols = ['tf', 'lookahead', 'set_profit_pct', 'sum_profit_pct', 'total_trades', 'n_open_trades']
    df = pd.DataFrame(res, columns=cols)
    df = df.sort_values('sum_profit_pct', ascending=False)

    # get win strategy:
    win_idx = df.index[0]
    win_sum_profit_pct = df['sum_profit_pct'].iloc[0]
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

    # print top strats
    with open(full_path_trades, 'a') as f:
        for idx, trades in enumerate(l_trades_str[:10]):
            print(f'#{idx}#', file=f)
            for trade in trades:
                print(trade, file=f)
