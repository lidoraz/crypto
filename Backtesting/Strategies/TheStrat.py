from Indicators import SMA, Volume, SupportResistanceLines2, ADX, TheStratInd, MACD
from .Strategy import *


class TheStrat(Strategy):
    """
        Dual strategy
    """

    def __init__(self, params=None):
        super().__init__('THESTRAT')
        if params is None:
            params = {}
        self._db = params.get('db')
        self.ema_slow_lk = params.get('sma_slow_lk', 150)  # 150
        self.ema_mid_lk = params.get('sma_mid_lk', 50)  # 150
        # self.crossed_ma_low_high = params.get('crossed_ma_low_high', True)
        self.ema_fast_lk = params.get('sma_fast_lk', 20)  # 50
        self.n_ema_soon = params.get('n_ema_soon', 3)
        self.max_stop_pct = params.get('max_stop_pct', 0.06)
        self.support_ahead = params.get('support_ahead', 10)
        self.risk_reward = params.get('risk_reward', 1.2)  # Risk reward profit / lose
        # Can back test this before going live, just need to add short
        self._ind_ema_slow = SMA(self.ema_slow_lk, color='darkred')  # long ema
        self._ind_ema_mid = SMA(self.ema_mid_lk, color='orange')  # trend
        # TODO: Think about using 3 emas, SLOW to MID cross will indicate SHORT / LONG trend change
        #  While corssing fast EMA to MID EMA will indicate if open a position or not.
        #  Looks good, still need some calibration, and, there is a major thing is that in realtime,
        #  It might be better to look on NOT FULL candles, so if there is a start of a trend, we want to catch it
        #  BEFORE the trend ends.
        self._ind_ema_fast = SMA(self.ema_fast_lk, color='cyan')
        # support resistance levels should be about 0.25% to 0.10%, really minor as the change in 1min small, disable fix_if, use different numbers if not found.
        self._ind_lines = SupportResistanceLines2(self.support_ahead, fix_if_too_close=False)
        self._ind_thestrat = TheStratInd(True, self._db)
        self._ind_rsi = MACD(14, display_signal=False)
        self._ind_vol = Volume(vol_ema=14)
        self._ind_adx = ADX()

    def add_indicators(self, df):
        tfs = ['5T', '15T', '1H', '4H', '1D', '1W']
        # Calculation must be done on multiple TF, getting confirmation on multiple is the key to win this
        # intraday will be - run on 5min, confirm on 15m, 1H, 4H, and 1D
        #  1d = request.tf('1D', symbol =BTC)
        #  1d.calc_confirm()
        #
        df = self.calc_indicators(df)
        ema_slow_col = self._ind_ema_slow.name
        ema_mid_col = self._ind_ema_mid.name

        # TODO: Check if difference in optimization whenever crossed is at low / high as before, and if MACD confirmation is useful.
        # buy condition
        df['green_candle_L'] = df['open'] < df['close']  # can use wick as well, to signal hammers
        df['uptrend'] = df['close'] > df[ema_slow_col]

        crossed_col_long = 'low'
        crossed_col_short = 'high'

        df['crossed_above'] = crossed_above(df[crossed_col_long], df[ema_mid_col], self.n_ema_soon)
        # df['crossed_trend_above'] = crossed_above(df['close'], df[ema_slow_col], self.n_ema_soon)
        # df['fast_above_mid_L'] = df[ema_fast_col] > df[ema_mid_col]

        # sell condition
        df['red_candle_S'] = df['open'] > df['close']
        df['downtrend'] = df['close'] < df[ema_slow_col]
        # high
        # CAN ADD SURGES: when in uptrend, and suddly become above the uptrend, look if
        df[f'crossed_below'] = crossed_below(df[crossed_col_short], df[ema_mid_col], self.n_ema_soon)
        # df['crossed_trend_below'] = crossed_below(df['close'], df[ema_slow_col], self.n_ema_soon)
        # df['fast_below_mid_S'] = df[ema_fast_col] < df[ema_mid_col]
        # Disable False signals if  BOTH EMAS are too close to each other (market is sideways)
        df['BUY_ALGO'] = df[f'uptrend'] & df['crossed_above'] & df['green_candle_L']
        df['SELL_ALGO'] = df[f'downtrend'] & df['crossed_below'] & df['red_candle_S']
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
