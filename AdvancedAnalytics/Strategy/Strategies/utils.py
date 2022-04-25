from AdvancedAnalytics.Strategy.data_wrappers import DataWrapper
from Crypto.DataProcessing.DataProvider import TIME_CONV


# TODO: Generalize this with other strategies
def mark_enter_exit_points(data_class: DataWrapper, indicator_func, params):
    """
    # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
    # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
    # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
    # STOP LOSS SETS ON THE LOWER BB
    # STOP LOSS SETS ON THE HIGHER BB on SELL
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """
    tf = params['tf']
    indicators_lookahead = params['lookahead']
    set_profit_pct = params['set_profit_pct']
    n_rsi_soon = params['n_rsi_soon']
    symbols = data_class.get_symbols()
    sum_pct = 0
    trades = []
    trades_str = []
    open_trades = 0
    for coin in symbols:
        df = data_class.get_data(coin, tf)
        df = indicator_func(df, indicators_lookahead, n_rsi_soon=n_rsi_soon)
        buy_idx = None
        coin_trade = []
        # sell_price_win_stop = -1
        # sell_price_lose_stop = -1
        for idx, row in df.iterrows():
            if not buy_idx:
                if row['BUY_ALGO_BBRSI']:
                    buy_idx = idx
                    sell_price_win_stop = row[f'BBTOP_{indicators_lookahead}']
                    sell_price_lose_stop = row[f'BBBOT_{indicators_lookahead}']
                    open_trades += 1
                    coin_trade.append(
                        {'coin': coin, 'buy': buy_idx.strftime(TIME_CONV), 'sell': None, 'profit_pct': None})

            else:
                sell_idx = idx
                buy_price = df['close'].loc[buy_idx]
                sell_price = df['close'].loc[sell_idx]
                hours_holding = (sell_idx - buy_idx).total_seconds() // 3600
                profit_pct = (sell_price / buy_price) - 1
                profit_pct_net = profit_pct - (0.001 * 2)  # plus commission
                sell_cause = None
                if True:
                    # if abs(profit_pct_net) > set_profit_pct:
                    if sell_price_win_stop < sell_price:  # and profit_pct > set_profit_pct
                        sell_cause = 'SELL_WIN_STOP'
                    elif sell_price_lose_stop > sell_price:  # and abs(profit_pct) > set_profit_pct
                        sell_cause = 'SELL_LOSE_STOP'
                    elif row['BUY_ALGO_BBRSI']:  # without 2nd if there are too many trades.
                        sell_cause = 'SELL_ALGO_BBRSI'

                if sell_cause:
                    coin_trade[-1]['sell'] = sell_idx.strftime(TIME_CONV)
                    coin_trade[-1]['profit_pct_net'] = profit_pct_net
                    trade_arr = [coin, sell_cause, buy_idx, round(buy_price, 2), sell_idx, round(sell_price, 2),
                                 hours_holding,
                                 f'{profit_pct:.2%}']
                    trade_arr = list(map(str, trade_arr))
                    transaction = 'Trade:' + "\t".join(trade_arr)
                    trades_str.append(transaction)
                    sum_pct += profit_pct
                    buy_idx = None
                    open_trades -= 1
        if len(coin_trade):
            trades.append(coin_trade)
    sum_pct = round(sum_pct, 4)
    print(f'tf={tf}, ahead={indicators_lookahead}, profit_pct={set_profit_pct}, sum_pct= {sum_pct:.2%}')
    return sum_pct, trades, trades_str, open_trades
