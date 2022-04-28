from Indicators import BollingerBands, SupportResistanceLines
from .Strategy import Strategy


class BB(Strategy):
    """
    # BUY ENTRY: First candle that closes below the bottom BB
    # SELL ENTRY: First candle that close upper the upper BB

    # WIN STOP SETS ON LAST RESISTANCE
    # LOSS STOP SETS ON LAST SUPPORT
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """

    def __init__(self, params, *args, **kwargs):
        super().__init__(params, *args, **kwargs)
        self.ind_ahead = params.get('BB_ind_ahead', 14)
        self.bb_std = params.get('BB_std', 2)
        self.ind_ahead = BollingerBands(self.ind_ahead, self.bb_std)
        self.ind_sr = SupportResistanceLines()
        # ind_sma = SMA(100)

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        df = df.join(self.ind_ahead.calc(df))
        df = df.join(self.ind_ahead.calc(df))

        df = df.dropna()
        df['OVER_BB'] = df[f'BBTOP_{self.ind_ahead}'] < df['close']
        df['BELOW_BB'] = df[f'BBBOT_{self.ind_ahead}'] > df['close']

        df['BUY_ALGO'] = df['BELOW_BB']
        df['SELL_ALGO'] = df['OVER_BB']

        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            # add stop-loss
            sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            return {'buy_idx': buy_idx,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}
