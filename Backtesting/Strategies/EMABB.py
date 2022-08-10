from Indicators import EMA, Volume, SupportResistanceLines2, BollingerBands
from .Strategy import *


class EMABB(Strategy):
    """
        INSANE Bollinger Bands + Moving Averages Strategy PROGRAMMED | +236% profit
        Inspired by this channel: https://www.youtube.com/watch?v=SzEkhpDbL1A&t=327s
        This strategy aims to work on the 1min tf, using mainly long EMA and vol to indicate change in trend and entry
        Dual strategy, can long and short
    """

    def __init__(self, params=None):
        super().__init__('EMABB')
        if params is None:
            params = {}
        self.ema_slow_lk = params.get('ema_slow_lk', 200)  # 150
        self.ema_fast_lk = params.get('ema_fast_lk', 50)  # 50
        self.n_bb_soon = params.get('n_bb_soon', 2)
        self.bb_lk = params.get('bb_lk', 20)
        self.bb_std = params.get('bb_std', 2.1)
        self.sl_pct = params.get('sl_pct', 0.005)  # 0.5%
        self.risk_reward = params.get('risk_reward', 1.2)  # Risk reward profit / lose
        self._ind_ema_slow = EMA(self.ema_slow_lk, color='white')
        self._ind_ema_fast = EMA(self.ema_fast_lk, color='yellow')
        self._ind_bb = BollingerBands(self.bb_lk, self.bb_std)
        # support resistance levels should be about 0.25% to 0.10%, really minor as the change in 1min small, disable fix_if, use different numbers if not found.
        # self._ind_lines = SupportResistanceLines2(self.support_ahead, fix_if_too_close=False)
        # self._ind_macd = MACD()

    def add_indicators(self, df):
        df = df.join(self._ind_ema_slow.calc(df))
        df = df.join(self._ind_ema_fast.calc(df))
        df = df.join(self._ind_bb.calc(df))
        # df = df.join(self._ind_lines.calc(df))
        ema_slow_col = self._ind_ema_slow.name
        ema_fast_col = self._ind_ema_fast.name
        bb_lk = self.bb_lk
        # GET IF CROSSED EMA ABOVE recently
        # df['engulfing_green_candle_L'] = (df['open'] < df['close'])
        df['green_candle'] = df['open'] < df['close']
        df['uptrend'] = df[ema_fast_col] > df[ema_slow_col]
        df['below_bb_bot'] = df.close < df[f'BBBOT_{bb_lk}']  # price now must close above the lower band
        df['was_below_bb_bot'] = df['below_bb_bot'].rolling(self.n_bb_soon).sum() > 0
        df['above_bb_bot'] = df.open > df[f'BBBOT_{bb_lk}']

        df['red_candle'] = df['open'] > df['close']
        df['downtrend'] = df[ema_fast_col] < df[ema_slow_col]
        df['above_bb_top'] = df.close > df[f'BBTOP_{bb_lk}']
        df['was_above_bb_top'] = df['above_bb_top'].rolling(self.n_bb_soon).sum() > 0
        df['below_bb_top'] = df.close < df[f'BBTOP_{bb_lk}']

        # check about adding specific candle stick, such as ignore signals with long top wick for long
        # or long bot wick for short
        df['BUY_ALGO'] = df['uptrend'] & df['was_below_bb_bot'] & df['above_bb_bot'] & df['green_candle']
        df['SELL_ALGO'] = df['downtrend'] & df['was_above_bb_top'] & df['below_bb_top'] & df['red_candle']

        df['support'] = df.low * (1 - self.sl_pct)
        df['resistance'] = df.high * (1 + self.sl_pct)
        # Test realtime futures with this open
        # df['BUY_ALGO'] = df['green_candle_L']
        # df['SELL_ALGO'] = df['red_candle_S']
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            sell_price_lose_stop = row['support']
            stop_loss, take_profit = calc_take_profit_price('buy', buy_price, sell_price_lose_stop, self.risk_reward)
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': take_profit,
                    'sell_price_lose_stop': stop_loss}

    def act_sell(self, idx, row):
        if row['SELL_ALGO']:
            sell_price = row['close']
            buy_price_lose_stop = row['resistance']
            stop_loss, take_profit = calc_take_profit_price('sell', sell_price, buy_price_lose_stop, self.risk_reward)
            return {'sell_idx': idx,
                    'sell_price': sell_price,
                    'buy_price_win_stop': take_profit,
                    'buy_price_lose_stop': stop_loss}
        # Does not really matter besides, that can sell in short and then support resistance switches places.
        pass
