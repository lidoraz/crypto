from Indicators import RSI, BollingerBands, SupportResistanceLines
from .Strategy import Strategy


class BB(Strategy):
    """
    # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
    # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
    # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
    # STOP LOSS SETS ON THE LOWER BB
    # STOP LOSS SETS ON THE HIGHER BB on SELL
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """

    def __init__(self, params, *args, **kwargs):
        super().__init__(params, *args, **kwargs)
        self.ind_ahead = params.get('RSIBB_ind_ahead', 14)
        self.ind_rsi = RSI(self.ind_ahead)
        self.ind_bb = BollingerBands(self.ind_ahead)
        self.ind_sr = SupportResistanceLines()
        # ind_sma = SMA(100)

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        df = df.join(self.ind_rsi.calc(df))
        df = df.join(self.ind_bb.calc(df))
        df = df.join(self.ind_sr.calc(df))
        # df = df.join(self.ind_sma.calc(df))
        df = df.dropna()
        df['OVER_BB'] = df[f'BBTOP_{self.ind_ahead}'] < df['close']
        df['BELOW_BB'] = df[f'BBBOT_{self.ind_ahead}'] > df['close']

        df['BUY_ALGO'] = df['BELOW_BB']
        df['SELL_ALGO'] = df['OVER_BB']

        return df

    def act(self, df):
        set_profit_pct = self.set_profit_pct
        sum_pct = 0
        trades_str = []
        buy_idx = None
        for idx, row in df.iterrows():
            if not buy_idx:
                if row['BUY_ALGO']:
                    buy_idx = idx
                    # add stop-loss
                    sell_price_win_stop = row['resistance']
                    sell_price_lose_stop = row['support']
            else:
                sell_idx = idx
                buy_price = df['close'].loc[buy_idx]
                sell_price = df['close'].loc[sell_idx]
                hours_holding = (sell_idx - buy_idx).total_seconds() // 3600
                profit_pct = (sell_price / buy_price) - 1
                profit_pct_net = profit_pct - (0.001 * 2)  # plus commission
                if set_profit_pct == 0 or (abs(profit_pct_net) > set_profit_pct > 0):
                    if sell_price_win_stop < sell_price:  # and profit_pct > set_profit_pct
                        sell_cause = 'SELL_WIN'
                    elif sell_price_lose_stop > sell_price:  # and abs(profit_pct) > set_profit_pct
                        sell_cause = 'SELL_LOSE'
                    elif row['SELL_ALGO']:  # without 2nd if there are too many trades.
                        sell_cause = 'SELL_ALGO'
                    else:
                        continue
                    trade_arr = [sell_cause, buy_idx, round(buy_price, 2),
                                 sell_idx, round(sell_price, 2), hours_holding, f'{profit_pct:.2%}']
                    trade_arr = list(map(str, trade_arr))
                    transaction = 'Trade:' + "\t".join(trade_arr)
                    trades_str.append(transaction)
                    sum_pct += profit_pct
                    buy_idx = None
        is_trade_open = buy_idx is not None
        return sum_pct, trades_str, is_trade_open

# TODO: Strategy: A better way to test stratgies is to compare each day the market, and look whenever there is a new oppertunity.
#  Selecting the best oppertunity should be chosen if wanted (maybe lowest RSI)
#  Next, maybe compare with a budget, and buying a trade with comparing other opportunities.

# it looks like lookahead of less than 5 is very volatile, need to restrict number of transactions
## Some coins do not change as frequent like GCOIN, so it is harder to count on the performance on these coins.
## 15Min trade made the highest value, but number of trades was very high as well and cannot be guaranteed.


#
# # print top trade config
# with open(full_path_trades, 'a') as f:
#     for idx, trades in enumerate(l_trades_str[:10]):
#         print(f'#{idx}#', file=f)
#         for trade in trades:
#             print(trade, file=f)
