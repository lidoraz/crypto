from Crypto.DataProcessing.DataProvider import TIME_CONV
from Crypto.DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data
from Crypto.DataProcessing.data_consts import COINS, START_DATA_DATE
from Crypto.DataProcessing.data_utils import extract_volume
import pandas as pd
from datetime import datetime
from Indicators import RSI, BollingerBands, SMA, CandleStick


def add_indicators(df, ind_ahead, n_rsi_soon=10):
    # n_rsi_soon: when RSI has alert, how forward to notify that alert
    ind_rsi = RSI(ind_ahead)
    ind_bb = BollingerBands(ind_ahead)
    ind_sma = SMA(100)
    df = df.join(ind_rsi.calc(df))
    df = df.join(ind_bb.calc(df))
    df = df.join(ind_sma.calc(df))
    df = df.dropna()

    rsi_col = f"RSI_{ind_ahead}"
    df['RSI_70'] = df[rsi_col] > 70  # has passed RSI 70
    df['RSI_30'] = df[rsi_col] < 30  # has passed RSI 30
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

    # add stop-loss
    df['SELL_WIN_STOP'] = df[f'BBTOP_{ind_ahead}'] < df['close']
    df['SELL_LOSE_STOP'] = df[f'BBBOT_{ind_ahead}'] > df['close']
    return df


def mark_enter_exit_points(df_prices, df_agg, tf, indicators_lookahead=14, set_profit_pct=0.05):
    """
    # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
    # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
    # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
    # STOP LOSS SETS ON THE LOWER BB
    # STOP LOSS SETS ON THE HIGHER BB on SELL
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """
    sum_pct = 0
    trades = []
    trades_str = []
    open_trades = 0
    # tODO: Arrange this trade vs trade_str - quite different
    for coin in COINS:
        _, volume = extract_volume(df_agg=df_agg, coin=coin, interval=tf)

        df = CandleStick(tf).calc(df_prices[coin])
        df = add_indicators(df, indicators_lookahead, n_rsi_soon=10)

        sell_causes = ['SELL_ALGO_BBRSI', 'SELL_WIN_STOP', 'SELL_LOSE_STOP']
        buy_idx = None
        coin_trade = []
        for idx, row in df.iterrows():
            if not buy_idx and row['BUY_ALGO_BBRSI']:
                buy_idx = idx
                open_trades += 1
                coin_trade.append({'coin': coin, 'buy': buy_idx.strftime(TIME_CONV), 'sell': None, 'profit_pct': None})
                continue
            is_sell_causes = [row[cause] for cause in sell_causes]
            is_sell_op = sum(is_sell_causes) > 0

            if buy_idx and is_sell_op:
                sell_cause = sell_causes[is_sell_causes.index(True)]
                sell_idx = idx
                buy_price = df['close'].loc[buy_idx]
                sell_price = df['close'].loc[sell_idx]
                hours_holding = (sell_idx - buy_idx).seconds // 3600
                profit_pct = (sell_price / buy_price) - 1
                should_sell = False
                # if hours_holding < 1:  # must hold for atleast an 2 hours
                #     continue
                win_causes = ['SELL_ALGO_BBRSI', 'SELL_WIN_STOP']
                if sell_cause in win_causes and profit_pct > set_profit_pct:  # sell cause we passed M Bollinder bands and RSI passed 70 # ▲▼
                    should_sell = True
                elif sell_cause == 'SELL_LOSE_STOP' and abs(profit_pct) > set_profit_pct / 2:
                    should_sell = True

                if should_sell:
                    coin_trade[-1]['sell'] = sell_idx.strftime(TIME_CONV)
                    coin_trade[-1]['profit_pct'] = profit_pct
                    trade_arr = [coin, sell_cause, buy_idx, buy_price, sell_idx, sell_price, hours_holding,
                                 f'{profit_pct:.2%}']
                    trade_arr = list(map(str, trade_arr))
                    transaction = 'Trade:' + "\t".join(trade_arr)
                    trades_str.append(transaction)
                    sum_pct += profit_pct
                    buy_idx = None
                    open_trades -= 1
        if len(coin_trade):
            trades.append(coin_trade)

    print('sum_pct', sum_pct)
    return sum_pct, trades, trades_str, open_trades


def find_optimal_BBRSI_strategy():
    print(datetime.now().strftime(TIME_CONV))
    # filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_agg = prepare_data(providers, START_DATA_DATE)

    # time_intervals = ['15Min', '1H']
    # lookaheads = range(5, 30, 2)
    # profit_pcts = [0.03, 0.05, 0.07, 0.10, 0.15]

    time_intervals = ['1H']
    lookaheads = range(10, 17, 2)
    profit_pcts = [0.03, 0.05, 0.07, 0.10, 0.15]

    # tf = '1H'
    # lookahead = 11
    # sum_pct, trades, trades_str = mark_enter_exit_points(df_prices, df_agg, tf, indicators_lookahead=14)
    # # print("\n".join(trades))
    # for trade in trades:
    #     print(trade)

    # TODO: it looks like lookahead of less than 5 is very volatile, need to restrict number of transactions
    ## Some coins do not change as frequent like GCOIN, so it is harder to count on the performance on these coins.
    ## 15Min trade made the highest value, but number of trades was very high as well and cannot be guaranteed.
    res = []
    l_trades = []
    l_trades_str = []
    for tf in time_intervals:  # ['5Min', '15Min', '1H', '4H']
        for lookahead in lookaheads:  # range(7, 30, 4):
            # for lookahead in [19]:  # range(7, 30, 4):
            for set_profit_pct in profit_pcts:
                sum_pct, trades, trades_str, n_open_trades = mark_enter_exit_points(df_prices, df_agg, tf, lookahead,
                                                                                    set_profit_pct)
                res.append([tf, lookahead, set_profit_pct, sum_pct, len(trades_str), n_open_trades])
                l_trades.append(trades)
                l_trades_str.append(trades_str)
    df = pd.DataFrame(res,
                      columns=['tf', 'lookahead', 'set_profit_pct', 'sum_profit_pct', 'total_trades', 'n_open_trades'])
    df = df.sort_values('sum_profit_pct', ascending=False)
    print(df)
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
    df_name = f'{time}_RSI_BB_stats.csv'
    win_trades_name = f'{time}_RSI_BB_trades.tsv'
    output_path = 'AdvancedAnalytics/strategy_output/'
    df.to_csv(output_path + df_name)
    with open(output_path + win_trades_name, 'w') as f:
        for trade in win_trades:
            print(trade, file=f)

    # print all strats
    with open(output_path + win_trades_name, 'a') as f:
        for idx, trades in enumerate(l_trades_str):
            print(f'#{idx}#', file=f)
            for trade in trades:
                print(trade, file=f)


if __name__ == '__main__':
    find_optimal_BBRSI_strategy()
    # TODO: Save win strategy, or whole trades with a JSON format.
    # df.tail()
