from Indicators import RSI, BollingerBands
from .Strategy import Strategy


class RsiBB(Strategy):
    """
    # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
    # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
    # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
    # STOP LOSS SETS ON THE LOWER BB
    # STOP LOSS SETS ON THE HIGHER BB on SELL
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """

    def __init__(self, params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if params is None:
            params = {}
        self.ind_ahead = params.get('RSIBB_ind_ahead', 14)
        self.n_rsi_soon = params.get('RSIBB_n_rsi_soon', 10)
        self.low_rsi = params.get('RSIBB_rsi_low', 30)
        self.high_rsi = params.get('RSIBB_rsi_high', 70)
        self.bb_std = params.get('RSIBB_BB_std', 2)
        self.ind_rsi = RSI(self.ind_ahead)
        self.ind_bb = BollingerBands(self.ind_ahead)
        # ind_sma = SMA(100)

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        df = df.join(self.ind_rsi.calc(df))
        df = df.join(self.ind_bb.calc(df))
        # df = df.join(self.ind_sma.calc(df))
        df = df.dropna()

        rsi_col = f"RSI_{self.ind_ahead}"
        df['RSI_70'] = df[rsi_col] > self.high_rsi  # has passed RSI 70
        df['RSI_30'] = df[rsi_col] < self.low_rsi  # has passed RSI 30
        df['OVER_BB'] = df[f'BBTOP_{self.ind_ahead}'] < df['close']
        df['BELOW_BB'] = df[f'BBBOT_{self.ind_ahead}'] > df['close']

        # buy condition
        df[f'RSI_BELOW_30_ROWS{self.n_rsi_soon}'] = df['RSI_30'].rolling(self.n_rsi_soon).sum() > 0
        df['OVER_MID_BB'] = df['close'] > df[f'SMA_{self.ind_ahead}']

        # sell condition
        df[f'RSI_OVER_70_ROWS{self.n_rsi_soon}'] = df['RSI_70'].rolling(self.n_rsi_soon).sum() > 0
        df[f'BELOW_MID_BB'] = df['close'] < df[f'SMA_{self.ind_ahead}']

        df['BUY_ALGO'] = df[f'RSI_BELOW_30_ROWS{self.n_rsi_soon}'] & df['OVER_MID_BB']
        df['SELL_ALGO'] = df[f'RSI_OVER_70_ROWS{self.n_rsi_soon}'] & df['BELOW_MID_BB']

        # # add stop-loss
        # # Handled during the DF iter rows
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            # add stop-loss
            sell_price_win_stop = row[f'BBTOP_{self.ind_ahead}']
            sell_price_lose_stop = row[f'BBBOT_{self.ind_ahead}']
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}
