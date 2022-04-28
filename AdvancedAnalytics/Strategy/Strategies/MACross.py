# TODO: For example, a simple trading strategy may be a moving average crossover whereby a short-term moving average
# crosses above or below a long-term moving average.
from AdvancedAnalytics.Strategy.DataWrap import NasdaqData
from .Strategy import Strategy
from Indicators import SMA, SupportResistanceLines


class MACross(Strategy):
    def __init__(self, params, short=25, long=100, *args, **kwargs):
        super().__init__(params, *args, **kwargs)
        self.short = params.get('MACROSS_short', short)
        self.long = params.get('MACROSS_long', long)

    def add_indicators(self, df):
        ind_short = SMA(self.short)
        ind_long = SMA(self.long)
        ind_sr = SupportResistanceLines()
        df = df.join(ind_short.calc(df))
        df = df.join(ind_long.calc(df))
        df = df.join(ind_sr.calc(df))
        df = df.dropna()

        df['BUY_ALGO'] = df[f'SMA_{self.short}'] > df[f'SMA_{self.long}']  # buy
        df['SELL_ALGO'] = df[f'SMA_{self.short}'] < df[f'SMA_{self.long}']  # sell
        return df

    # TODO: write buy act, act buy act sell
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
                # TODO: take out commision

                if set_profit_pct == 0 or (abs(profit_pct_net) > set_profit_pct > 0):  # pure algo or become greedy
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


if __name__ == '__main__':
    data_wrapper = NasdaqData.get_wrapper(start_date='2016-01-01')
    df = data_wrapper.get_data('AAPL', tf='1D')
    add_indicators(df)
