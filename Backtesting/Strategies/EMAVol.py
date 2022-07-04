from Indicators import EMA, Volume, SupportResistanceLines2, MACD
from .Strategy import Strategy


# Scalping strategy, only for 1, 5 min timeframes.


class EMAVol(Strategy):
    """
        Inspired by this channel: https://www.youtube.com/watch?v=Dmh0BfJURTM
        This strategy aims to work on the 1min tf, using mainly long EMA and vol to indicate change in trend and entry
        Dual strategy, can long and short
    """

    def __init__(self, params=None):
        super().__init__('EMAVOL')
        if params is None:
            params = {}
        self.ema_ahead = params.get('ema_ahead', 200)  # 150
        self.n_ema_soon = params.get('n_ema_soon', 10)
        self.vol_ema = params.get('vol_ema', 20)
        self.support_ahead = params.get('support_ahead', 20)
        # Can back test this before going live, just need to add short
        self._ind_ema = EMA(self.ema_ahead, color='white')  # long ema
        self._ind_ema_2 = EMA(50, color='purple')
        # support resistance levels should be about 0.25% to 0.10%, really minor as the change in 1min small, disable fix_if, use different numbers if not found.
        self._ind_lines = SupportResistanceLines2(self.support_ahead, fix_if_too_close=False)
        self._ind_macd = MACD()
        self._ind_vol = Volume(vol_ema=self.vol_ema)

    def add_indicators(self, df):
        df = df.join(self._ind_vol.calc(df))
        df = df.join(self._ind_macd.calc(df))
        df = df.join(self._ind_ema.calc(df))
        df = df.join(self._ind_ema_2.calc(df))
        df = df.join(self._ind_lines.calc(df))
        ema_col = self._ind_ema.ra.name
        ema_fast_col = self._ind_ema_2.ra.name
        df['volume_over'] = df.volume > df[f'volume_EMA{self._ind_vol.vol_ema}'] * 1.01
        # buy condition
        # (df['close'] > df[ema_col]).rolling(self.n_ema_soon).sum()
        # (df['close'] > df[ema_col]).rolling(self.n_ema_soon).sum() > 0
        # df['above_ema'].rolling(5).sum() > 0
        min_candles_af_area = 1
        # GET IF CROSSED EMA ABOVE recently
        df['above_ema'] = (df['close'] > df[ema_col]) & (df['open'] > df[ema_col])
        df[f'was_above_before'] = df['above_ema'].rolling(self.n_ema_soon).sum() >= min_candles_af_area
        df['green_candle'] = df['open'] < df['close']  # can use wick as well, to signal hammers
        df['fast_above_slow'] = df[ema_fast_col] > df[ema_col]
        # sell condition
        df[f'below_ema'] = (df['open'] < df[ema_col]) & (df['close'] < df[ema_col])
        df[f'was_below_before'] = df['below_ema'].rolling(self.n_ema_soon).sum() >= min_candles_af_area
        df['red_candle'] = df['open'] > df['close']
        df['fast_below_slow'] = df[ema_fast_col] < df[ema_col]

        df['BUY_ALGO'] = df[f'was_below_before'] & df['above_ema'] \
                         & df['volume_over'] & df['green_candle'] & df['fast_above_slow']
        df['SELL_ALGO'] = df[f'was_above_before'] & df['below_ema'] \
                          & df['volume_over'] & df['red_candle'] & df['fast_below_slow']
        #
        # df['BUY_ALGO'] = df['above_ema']
        # df['SELL_ALGO'] = df['below_ema']
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}

    def act_sell(self, idx, row):
        if row['SELL_ALGO']:
            sell_price = row['close']
            buy_price_win_stop = row['support']
            buy_price_lose_stop = row['resistance']  # can be 1:1  risk reward, copy code from short binance
            return {'sell_idx': idx,
                    'sell_price': sell_price,
                    'buy_price_win_stop': buy_price_win_stop,
                    'buy_price_lose_stop': buy_price_lose_stop}
        # Does not really matter besides, that can sell in short and then support resistance switches places.
        pass
