from Indicators import StochRSI, SMA, SupportResistanceLines2
from .Strategy import Strategy


class SMAStochRSI(Strategy):
    """

    """

    def __init__(self, params=None):
        super().__init__('RSISTO')
        if params is None:
            params = {}
        self.rsi_ahead = params.get('rsi_ahead', 14)
        self.rsi_smooth = 5
        self.rsi_high = 80
        self.rsi_low = 20
        self.n_rsi_soon = 5
        self.sma_ahead = params.get('sma_ahead', 10)
        self.support_ahead = params.get('support_ahead', 70)

        self._ind_rsi = StochRSI(self.rsi_ahead, self.rsi_smooth)
        self._ind_sma = SMA(self.sma_ahead)
        self._ind_lines = SupportResistanceLines2(self.support_ahead)
        self.tolerance_close = 0.03

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        df = df.join(self._ind_rsi.calc(df))
        df = df.join(self._ind_sma.calc(df))
        df = df.join(self._ind_lines.calc(df))

        # rsi_col = f"RSI_{self.rsi_ahead}"
        df['StochRSI_above'] = df[self._ind_rsi.ra.name] > self.rsi_high  # has passed RSI 70
        df['StochRSI_below'] = df[self._ind_rsi.ra.name] < self.rsi_low  # has passed RSI 30

        # buy condition
        df[f'RSI_BELOW_ROWS'] = df['StochRSI_below'].rolling(self.n_rsi_soon).sum() > 0
        df['OVER_MID'] = df['close'] > df[self._ind_sma.ra.name] * (1 - self.tolerance_close)

        # sell condition
        df[f'RSI_ABOVE_ROWS'] = df['StochRSI_above'].rolling(self.n_rsi_soon).sum() > 0
        df[f'BELOW_MID'] = df['close'] < df[self._ind_sma.ra.name] * (1 + self.tolerance_close)

        df['BUY_ALGO'] = df[f'RSI_BELOW_ROWS'] & df['OVER_MID']
        df['SELL_ALGO'] = df[f'RSI_ABOVE_ROWS'] & df['BELOW_MID']

        # # add stop-loss
        # # Handled during the DF iter rows
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            # add stop-loss
            sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}

