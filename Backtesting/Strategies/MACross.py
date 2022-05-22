# TODO: For example, a simple trading strategy may be a moving average crossover whereby a short-term moving average
# crosses above or below a long-term moving average.
from .Strategy import Strategy
from Indicators import SMA, SupportResistanceLines


class MACross(Strategy):
    def __init__(self, params=None, short=25, long=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if params is None:
            params = {}
        self.short = params.get('MACROSS_short', short)
        self.long = params.get('MACROSS_long', long)

    def add_indicators(self, df):
        ind_short = SMA(self.short)
        ind_long = SMA(self.long)
        ind_sr = SupportResistanceLines()
        df = df.join(ind_short.calc(df))
        df = df.join(ind_long.calc(df))
        df = df.join(ind_sr.calc(df))
        # df = df.dropna()

        df['BUY_ALGO'] = df[f'SMA_{self.short}'] > df[f'SMA_{self.long}']
        df['SELL_ALGO'] = df[f'SMA_{self.short}'] < df[f'SMA_{self.long}']
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            # add stop-loss
            buy_price = row['close']
            # TODO: It is possible to calculate current resistance support and resistance from here.
            #  It will be very slow when trying to backttesting...
            sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}
