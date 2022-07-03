from Indicators import EMA, Volume, SupportResistanceLines2, MACD
from .Strategy import Strategy


# Scalping strategy, only for 1, 5 min timeframes.


class EMAVol(Strategy):
    """

    """

    def __init__(self, params=None):
        super().__init__('EMAVOL')
        if params is None:
            params = {}
        self.ema_ahead = params.get('ema_ahead', 99)
        self.n_ema_soon = params.get('n_ema_soon', 5)
        self.vol_ema = params.get('vol_ema', 7)
        self.support_ahead = params.get('support_ahead', 20)

        self._ind_ema = EMA(self.ema_ahead, color='white')  # long ema
        self._ind_ema_2 = EMA(20, color='purple')
        self._ind_lines = SupportResistanceLines2(self.support_ahead)
        self._ind_macd = MACD()
        self._ind_vol = Volume(vol_ema=self.vol_ema)

    def add_indicators(self, df):
        df = df.join(self._ind_vol.calc(df))
        df = df.join(self._ind_macd.calc(df))
        df['volume_over'] = df.volume > df[f'volume_EMA{self._ind_vol.vol_ema}'] * 1.01
        df = df.join(self._ind_ema.calc(df))
        df = df.join(self._ind_lines.calc(df))
        ema_col = self._ind_ema.ra.name
        # buy condition
        # (df['close'] > df[ema_col]).rolling(self.n_ema_soon).sum()
        # (df['close'] > df[ema_col]).rolling(self.n_ema_soon).sum() > 0
        # df['above_ema'].rolling(5).sum() > 0
        min_candles_af_area = 1
        df['above_ema'] = (df['close'] > df[ema_col]) & (df['open'] > df[ema_col])
        # GET IF CROSSED EMA ABOVE recently
        df[f'was_above_before'] = df['above_ema'].rolling(self.n_ema_soon).sum() >= min_candles_af_area

        # sell condition
        df[f'below_ema'] = (df['open'] < df[ema_col]) & (df['close'] < df[ema_col])
        df[f'was_below_before'] = df['below_ema'].rolling(self.n_ema_soon).sum() >= min_candles_af_area

        df['BUY_ALGO'] = df[f'was_below_before'] & df['above_ema'] & df['volume_over']
        df['SELL_ALGO'] = df[f'was_above_before'] & df['below_ema'] & df['volume_over']

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

    def act_sell(self):
        # Does not really matter besides, that can sell in short and then support resistance switches places.
        pass
