from Indicators import EMA, Volume, SupportResistanceLines2, MACD, MFI, ADX, RSI
from .Strategy import *


class S2(Strategy):
    """
        Dual strategy
        Using Only EMA 200 to calculate trend and short / long depending on derivative
    """

    def __init__(self, params=None):
        super().__init__('S2')
        if params is None:
            params = {}
        self.ema_slow_lk = params.get('ema_slow_lk', 200)  # 150
        self.max_stop_pct = params.get('max_stop_pct', 0.06)
        self.support_ahead = params.get('support_ahead', 10)
        self.risk_reward = params.get('risk_reward', 1.2)  # Risk reward profit / lose
        # Can back test this before going live, just need to add short
        self._ind_ema_slow = EMA(self.ema_slow_lk, color='white')  # long ema
        # TODO: Think about using 3 emas, SLOW to MID cross will indicate SHORT / LONG trend change
        #  While corssing fast EMA to MID EMA will indicate if open a position or not.
        #  Looks good, still need some calibration, and, there is a major thing is that in realtime,
        #  It might be better to look on NOT FULL candles, so if there is a start of a trend, we want to catch it
        #  BEFORE the trend ends.
        # self._ind_ema_fast = EMA(self.ema_fast_lk, color='purple')
        # support resistance levels should be about 0.25% to 0.10%, really minor as the change in 1min small, disable fix_if, use different numbers if not found.
        self._ind_lines = SupportResistanceLines2(self.support_ahead, fix_if_too_close=False)
        self._ind_vol = Volume(vol_ema=14)

    def add_indicators(self, df):
        df = self.calc_indicators(df, dropna=True)

        ema_slow_col = self._ind_ema_slow.name

        # buy condition
        df['green_candle_L'] = df['open'] < df['close']  # can use wick as well, to signal hammers

        def calc_slope(series, lookback):
            def first(rows):
                return rows.iloc[0]

            def last(rows):
                return rows.iloc[-1]

            return (series.rolling(lookback).apply(last) / series.rolling(lookback).apply(first)) - 1

        df['crossed_above'] = crossed_above(df.close, df[ema_slow_col], 3)
        df['slope'] = calc_slope(df[ema_slow_col], 50)
        df['uptrend'] = df['slope'] > 0.01  # maybe larger than x
        df['downtrend'] = df['slope'] < -0.01
        print(df['slope'])
        df['red_candle_S'] = df['open'] > df['close']
        df['crossed_below'] = crossed_below(df.close, df[ema_slow_col], 3)
        df['BUY_ALGO'] = False
        df['SELL_ALGO'] = False
        df['BUY_ALGO'] = df[f'uptrend'] & df['crossed_above'] & df['green_candle_L']
        df['SELL_ALGO'] = df[f'downtrend'] & df['crossed_below'] & df['red_candle_S']
        df = df.dropna()
        # df['BUY_ALGO'] = df['BUY_ALGO'] | (df['volume_over'] & df['uptrend'] & df['green_candle_L'])
        # df['SELL_ALGO'] = df['SELL_ALGO'] | (df['volume_over'] & df['downtrend'] & df['red_candle_S'])
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            # sell_price_win_stop = row['resistance']
            sell_price_lose_stop = row['support']
            stop_loss, take_profit = calc_take_profit_price('buy', buy_price, sell_price_lose_stop, self.risk_reward,
                                                            self.max_stop_pct)
            # tp -> 0.5 at 1.5, 0.25 at 2.0, 0.25 at 2.5
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': take_profit,
                    'sell_price_lose_stop': stop_loss}

    def act_sell(self, idx, row):
        if row['SELL_ALGO']:
            sell_price = row['close']
            buy_price_lose_stop = row['resistance']  # can be 1:1  risk reward, copy code from short binance
            stop_loss, take_profit = calc_take_profit_price('sell', sell_price, buy_price_lose_stop, self.risk_reward,
                                                            self.max_stop_pct)
            return {'sell_idx': idx,
                    'sell_price': sell_price,
                    'buy_price_win_stop': take_profit,
                    'buy_price_lose_stop': stop_loss}
        # Does not really matter besides, that can sell in short and then support resistance switches places.
        pass
