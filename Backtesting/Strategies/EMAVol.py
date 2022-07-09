from Indicators import EMA, Volume, SupportResistanceLines2, MACD
from .Strategy import Strategy


def calc_take_profit_price(side, price, stop_loss, rw_ratio=1.0):
    assert side in ('buy', 'sell')
    pct_to_curr_price = 0.001
    price_to_stop = abs(price - stop_loss)
    if side == 'buy':  # long
        if price / stop_loss <= 1 + pct_to_curr_price:  # should be larger than 1.001
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 - pct_to_curr_price)
            take_profit = price * (1 + pct_to_curr_price)
        else:
            take_profit = price + rw_ratio * price_to_stop
    else:  # short
        if price / stop_loss >= 1 - pct_to_curr_price:  # should be less than 0.999
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 + pct_to_curr_price)
            take_profit = price * (1 - pct_to_curr_price)
        else:
            take_profit = price - rw_ratio * price_to_stop

    return stop_loss, take_profit


class EMAVol(Strategy):
    """
        # Scalping strategy, only for 1, 5 min timeframes.
        Inspired by this channel: https://www.youtube.com/watch?v=Dmh0BfJURTM
        This strategy aims to work on the 1min tf, using mainly long EMA and vol to indicate change in trend and entry
        Dual strategy, can long and short
    """

    def __init__(self, params=None):
        super().__init__('EMAVOL')
        if params is None:
            params = {}
        self.ema_ahead = params.get('ema_ahead', 180)  # 150
        self.n_ema_soon = params.get('n_ema_soon', 7)
        self.ema_fast_ahead = params.get('ema_fast_ahead', 25)  # 50
        self.vol_ema = params.get('vol_ema', 20)
        self.support_ahead = params.get('support_ahead', 20)
        self.risk_reward = params.get('risk_reward', 1.2)  # Risk reward profit / lose
        # Can back test this before going live, just need to add short
        self._ind_ema = EMA(self.ema_ahead, color='white')  # long ema
        self._ind_ema_2 = EMA(self.ema_fast_ahead, color='purple')
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
        df['green_candle_L'] = df['open'] < df['close']  # can use wick as well, to signal hammers
        # df['engulfing_green_candle_L'] = (df['open'] < df['close'])
        df['above_ema_L'] = (df['close'] > df[ema_col]) & (df['open'] > df[ema_col])
        df[f'was_above_ema_S'] = df['above_ema_L'].rolling(self.n_ema_soon).sum() >= min_candles_af_area
        df['fast_above_slow_L'] = df[ema_fast_col] > df[ema_col]
        # sell condition
        df['red_candle_S'] = df['open'] > df['close']
        df[f'below_ema_S'] = (df['open'] < df[ema_col]) & (df['close'] < df[ema_col])
        df[f'was_below_ema_L'] = df['below_ema_S'].rolling(self.n_ema_soon).sum() >= min_candles_af_area
        df['fast_below_slow_S'] = df[ema_fast_col] < df[ema_col]

        # df['BUY_ALGO'] = df[f'was_below_ema_L'] & df['above_ema_L'] \
        #                  & df['volume_over'] & df['green_candle_L'] & df['fast_above_slow_L']
        # df['SELL_ALGO'] = df[f'was_above_ema_S'] & df['below_ema_S'] \
        #                   & df['volume_over'] & df['red_candle_S'] & df['fast_below_slow_S']
        # Moran add, switch pos, maybe move to higher tf
        df['SELL_ALGO'] = df[f'was_below_ema_L'] & df['above_ema_L'] \
                         & df['volume_over'] & df['fast_above_slow_L'] & df['red_candle_S']
        df['BUY_ALGO'] = df[f'was_above_ema_S'] & df['below_ema_S'] \
                          & df['volume_over'] & df['fast_below_slow_S'] & df['green_candle_L']
        # df['BUY_ALGO'] = df['above_ema']
        # df['SELL_ALGO'] = df['below_ema']
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            # sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            stop_loss, take_profit = calc_take_profit_price('buy', buy_price, sell_price_lose_stop, self.risk_reward)
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': take_profit,
                    'sell_price_lose_stop': stop_loss}

    def act_sell(self, idx, row):
        if row['SELL_ALGO']:
            sell_price = row['close']
            buy_price_lose_stop = row['resistance']  # can be 1:1  risk reward, copy code from short binance
            stop_loss, take_profit = calc_take_profit_price('sell', sell_price, buy_price_lose_stop, self.risk_reward)
            return {'sell_idx': idx,
                    'sell_price': sell_price,
                    'buy_price_win_stop': take_profit,
                    'buy_price_lose_stop': stop_loss}
        # Does not really matter besides, that can sell in short and then support resistance switches places.
        pass
