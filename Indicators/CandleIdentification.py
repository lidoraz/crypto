from plotly import graph_objects as go
from .Indicator import get_marker_color_candle, Indicator
import pandas as pd
import numpy as np
import talib

from .utils.candle_rankings import candle_rankings


# Note - 1
# Only some patterns have bull and bear versions.
# However, to make the process unified and for codability purposes
# all patterns are labeled with "_Bull" and "_Bear" tags.
# Both versions of the single patterns are given same performance rank,
# since they will always return only 1 version.

# Note - 2
# Following TA-Lib patterns are excluded from the analysis since the corresponding ranking not found:
# CounterAttack, Longline, Shortline, Stalledpattern, Kickingbylength


def apply_on_patterns(row):
    def convert_to_pattern_trend(k, v):
        if v > 0:
            return k + '_Bull'
        elif v < 0:
            return k + '_Bear'

    patterns = row[row != 0]
    if len(patterns) == 0:
        return 'na', None, 0
    k, v = list(zip(*patterns.to_dict().items()))
    if len(patterns) == 1:  # not zero there is signal
        k_with_trend = convert_to_pattern_trend(k[0], v[0])
        return k_with_trend, candle_rankings[k_with_trend], 1
    else:  # larger than 1
        k_with_trend = [convert_to_pattern_trend(k, v) for k, v in zip(k, v)]
        ranking = [candle_rankings[k] for k in k_with_trend]
        return k_with_trend[np.argmin(ranking)], ranking[np.argmin(ranking)], len(patterns)


def define_trend(x):
    if x.endswith('_Bull'):
        return 1
    elif x.endswith('_Bear'):
        return -1
    else:
        return 0


# Best Performance candlestick pattern matched by www.thepatternsite.com
# https://medium.com/analytics-vidhya/recognizing-over-50-candlestick-patterns-with-python-4f02a1822cb5
# Read more at: - https://academy.binance.com/en/articles/beginners-candlestick-patterns
def recognize_candles(df):
    """
    Recognizes candlestick patterns and Returns a df with these columns:
    'best_pattern - best pattern found by strength based by www.thepatternsite.com'
    'best_trend - best strength pattern multiplied by bull / bear (1, -1)
    'n_patterns - number of matching patterns found'
    """
    df = df.copy()
    op = df['open'].astype(float)
    hi = df['high'].astype(float)
    lo = df['low'].astype(float)
    cl = df['close'].astype(float)

    patterns = talib.get_function_groups()['Pattern Recognition']

    # patterns not found in the patternsite.com
    exclude_items = ('CDLCOUNTERATTACK',
                     'CDLLONGLINE',
                     'CDLSHORTLINE',
                     'CDLSTALLEDPATTERN',
                     'CDLKICKINGBYLENGTH')

    patterns = [pattern for pattern in patterns if pattern not in exclude_items]

    for pattern in patterns:
        # df["CDL3LINESTRIKE"] = talib.CDL3LINESTRIKE(op, hi, lo, cl)
        df[pattern] = getattr(talib, pattern)(op, hi, lo, cl)

    # apply a function on all detected patterns to find strongest one
    res = df[patterns].apply(apply_on_patterns, axis=1, result_type='expand')
    res.columns = ['best_pattern', 'best_ranking', 'n_patterns']

    res['best_trend'] = res['best_pattern'].apply(define_trend)
    res['best_pattern'] = res['best_pattern'].apply(lambda x: x.split('_')[0][3:] if x is not None else x)

    return res


class CandleIdentification(Indicator):
    def __init__(self, normalize_detected_patterns=True, plot_loc=None):
        self.normalize_detected_patterns = normalize_detected_patterns
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.res = None
        self.ohlc = None

    def calc(self, ohlc: pd.DataFrame) -> pd.DataFrame:
        self.res = recognize_candles(ohlc)
        self.ohlc = ohlc
        return self.res

    def plot(self, fig):
        df_patterns = self.res
        df_patterns['plot_value'] = (104 - df_patterns['best_ranking']) * df_patterns['best_trend']
        if self.normalize_detected_patterns:
            df_patterns['plot_value'] = df_patterns['plot_value'] * (1 / df_patterns['n_patterns'])

        #  match candle color to pattern color
        marker_color = get_marker_color_candle(self.ohlc)
        # marker_color = ['Green' if x > 0 else 'Red' for x in df_patterns['plot_value']]
        text = df_patterns['best_pattern'] + '(' + df_patterns['n_patterns'].astype(str) + ')'
        trace = go.Bar(y=df_patterns['plot_value'], x=df_patterns.index, text=text,
                       # f'PatternCertainty'
                       name=f'PTRN(STR)',  # textposition="outside",
                       marker_color=marker_color)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
