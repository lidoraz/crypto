from Indicators import RSI, MACD, SupportResistanceLines2, SMA, EMA
from .Strategy import Strategy


class SMAMACD(Strategy):
    """
    # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
    # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
    # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
    # STOP LOSS SETS ON THE LOWER BB
    # STOP LOSS SETS ON THE HIGHER BB on SELL
    https://www.youtube.com/watch?v=yBjk9r9igcQ
    """

    def __init__(self, params=None):
        super().__init__('MACD')
        if params is None:
            params = {}
        # self.aggressive = params.get('RSIBB_aggressive', False)
        # self.rsi_ahead = params.get('RSIBB_rsi_ahead', 14)
        # self.rsi_low = params.get('RSIBB_rsi_low', 30)
        # self.rsi_high = params.get('RSIBB_rsi_high', 70)
        self.n_macd_soon = params.get('n_macd_soon', 5)
        # self.macd_quantile = params.get('macd_quantile', 0.15)
        self.lk_short = params.get('short', 20)
        self.lk_long = 99

        # self._ind_rsi = RSI(self.rsi_ahead)
        self._ind_macd = MACD()
        self._ind_short = SMA(self.lk_short, color='purple')
        self._ind_long = EMA(self.lk_long, color='cyan')
        self._ind_lines = SupportResistanceLines2(lookback_length=100)
        # self._ind_bb = BollingerBands(self.bb_ahead, self.bb_std)

    def add_indicators(self, df):
        # n_rsi_soon: when RSI has alert, how forward to notify that alert
        # df = df.join(self._ind_rsi.calc(df))
        df = df.join(self._ind_macd.calc(df))
        df = df.join(self._ind_lines.calc(df))
        df = df.join(self._ind_short.calc(df))
        df = df.join(self._ind_long.calc(df))
        # df = df.dropna()

        # cant use this as need to be calculated on rolling.
        # macd_threshold_low = df['MCAD_HIST'].abs().quantile(self.macd_quantile)  # over 05%
        # macd_threshold_high = df['MCAD_HIST'].abs().quantile(self.macd_quantile + 0.05)
        # # if macd_threshold.any():
        # #     print('have')
        # df['MACD_UPTREND'] = (df['MCAD_HIST'] >= macd_threshold_low) & (df['MCAD_HIST'] < macd_threshold_high)   # has passed RSI 70
        # df['MACD_DOWNTREND'] = (df['MCAD_HIST'] < -macd_threshold_low) & (df['MCAD_HIST'] > -macd_threshold_high)  # has passed RSI 30
        # TODO: Still not very good, but i think this is the way.
        df['MACD_UPTREND'] = (df['MCAD_HIST'] > 0) & (df['MCAD_HIST'].pct_change(periods=2) > 7.0)
        df['MACD_DOWNTREND'] = (df['MCAD_HIST'] < 0) & (df['MCAD_HIST'].pct_change(periods=2) < -7.0)
        # # buy condition
        df[f'MACD_UPTREND_BEFORE'] = df['MACD_UPTREND'].rolling(self.n_macd_soon).sum() > 0
        # # sell condition
        df[f'MACD_DOWNTREND_BEFORE'] = df['MACD_DOWNTREND'].rolling(self.n_macd_soon).sum() > 0

        df['BUY_ALGO'] = df[f'MACD_UPTREND_BEFORE'] & (df[f'SMA_{self.lk_short}'] < df.close)
        df['SELL_ALGO'] = df[f'MACD_DOWNTREND_BEFORE'] & (df[f'SMA_{self.lk_short}'] > df.close)
        return df

    def act_buy(self, idx, row):
        if row['BUY_ALGO']:
            buy_idx = idx
            buy_price = row['close']
            # add stop-loss
            # sell_price_win_stop = buy_price * 1.15#
            # sell_price_lose_stop = buy_price * .90
            sell_price_win_stop = row[f'resistance']  # * 1.05
            sell_price_lose_stop = row[f'support']
            return {'buy_idx': buy_idx,
                    'buy_price': buy_price,
                    'sell_price_win_stop': sell_price_win_stop,
                    'sell_price_lose_stop': sell_price_lose_stop}
