from Indicators import StochRSI, SMA, SupportResistanceLines2
from .Strategy import Strategy


class SMAStochRSI(Strategy):
    """

    """

    def __init__(self, params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if params is None:
            params = {}
        self.name = 'SMAStochRSI'
        # self.aggressive = params.get('RSIBB_aggressive', False)
        self.rsi_ahead = 14  # params.get('RSIBB_rsi_ahead', 14)
        # self.bb_ahead = params.get('RSIBB_bb_ahead', 20)
        # self.bb_std = params.get('RSIBB_bb_std', 2)
        # self.n_rsi_soon = params.get('RSIBB_n_rsi_soon', 10)
        # self.low_rsi = params.get('RSIBB_rsi_low', 30)
        # self.high_rsi = params.get('RSIBB_rsi_high', 70)
        self.ind_rsi = StochRSI(14, 5)
        self.high_rsi = 80
        self.low_rsi = 20
        self.n_rsi_soon = 5
        self.ind_sma = SMA(12)
        self.ind_lines = SupportResistanceLines2(70)
        # print(f'RSIBB {}')
        # ind_sma = SMA(100)

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        df = df.join(self.ind_rsi.calc(df))
        df = df.join(self.ind_sma.calc(df))
        df = df.join(self.ind_lines.calc(df))

        # rsi_col = f"RSI_{self.rsi_ahead}"
        df['StochRSI_above'] = df[self.ind_rsi.ra.name] > self.high_rsi  # has passed RSI 70
        df['StochRSI_below'] = df[self.ind_rsi.ra.name] < self.low_rsi  # has passed RSI 30

        # buy condition
        df[f'RSI_BELOW_ROWS'] = df['StochRSI_below'].rolling(self.n_rsi_soon).sum() > 0
        df['OVER_MID'] = df['close'] > df[self.ind_sma.ra.name]

        # sell condition
        df[f'RSI_ABOVE_ROWS'] = df['StochRSI_above'].rolling(self.n_rsi_soon).sum() > 0
        df[f'BELOW_MID'] = df['close'] < df[self.ind_sma.ra.name]

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

    def __repr__(self):
        return 'SMAStochRSI'
