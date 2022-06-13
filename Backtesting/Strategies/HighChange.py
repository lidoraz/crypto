# TODO: For example, a simple trading strategy may be a moving average crossover whereby a short-term moving average
# crosses above or below a long-term moving average.
from .Strategy import Strategy
from Indicators import Volume, SMA


class HighChange(Strategy):
    def __init__(self, params=None):
        super().__init__('HIGHCHANGE')
        if params is None:
            params = {}
        # 0.01 for 15min, 0.05 for 1H
        self.pct = params.get('pct', 0.01)
        # self.smoo = params.get('long', long)
        self._vol = Volume()

    def add_indicators(self, df):
        df = df.join(self._vol.calc(df))
        df['volume_over'] = df[f'volume_EMA{self._vol.smooth_factor}'] * 1.2 < df.volume
        df['pct_close'] = df.close.pct_change()
        # find high candle
        # df['high_low'] = df['high'] - df['low']
        # df['high_low_smooth'] = df['high_low'].rolling(7).mean() + 2 * df['high_low'].rolling(7).std()
        # df['over_high_low'] = df['high_low'] > df['high_low_smooth']
        # df['below_high_low'] = df['high_low'] < df['high_low_smooth']
        df['pct_close_high'] = df['pct_close'] > self.pct
        df['pct_close_low'] = df['pct_close'] < -self.pct
        # df = df.dropna()
        df['buy_pct_vol'] = (df['volume_over']) & (df['pct_close_high'])
        df['sell_pct_vol'] = (df['volume_over']) & (df['pct_close_low'])
        # df['buy_diff_vol'] = (df['volume_over']) & (df['over_high_low'])
        # df['sell_diff_vol'] = (df['volume_over']) & (df['below_high_low'])
        df['BUY_ALGO'] = (df['buy_pct_vol'])  # | (df['buy_diff_vol'])
        df['SELL_ALGO'] = (df['sell_pct_vol'])  # | (df['sell_diff_vol'])
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            sell_price_win_stop = buy_price * 1.15
            sell_price_lose_stop = buy_price * 0.9
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}

