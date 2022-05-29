import os

from Dashboard.Plots.plotly_fig import get_updated_fig
from Data.Crypto.ccxt_utils import get_candles_from_db
from Data.Crypto.symbols import exchange_symbol_pairs, DB_PATH
from Indicators.utils.candle_rankings import candle_rankings
from Utils import Persistence
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(root)
print(root)
db = Persistence(DB_PATH)
from Indicators import SupportResistanceLines2, Volume, RSI, SMA, CandleIdentification


def run_candle_idetification():
    # exchange_symbol_pairs
    coin = 'BTC'
    tf = '15min'
    df_ohlcv = get_candles_from_db(db, coin, tf, start_date='2022-05-01', localize=None)
    df_ohlcv = df_ohlcv[df_ohlcv.index <= pd.to_datetime('2022-05-10T12:00:00', utc=True)]
    main_plot_indicators = [
        SMA(7, color='orange'),
        SMA(25, color='purple'),
        SMA(100, color='cyan'),
        SupportResistanceLines2(lookback_length=100, plot_index=-1)]
    sub_plots = [
        # Volume(),
        CandleIdentification(False),
        RSI(14),
    ]
    fig, df_ohlcv = get_updated_fig(df_ohlcv, main_plot_indicators, sub_plots, xy_limit=False, with_data=True)
    best_candles = {"CDL3LINESTRIKE_Bull": 1,
                    "CDL3LINESTRIKE_Bear": 2,
                    "CDL3BLACKCROWS_Bull": 3,
                    "CDL3BLACKCROWS_Bear": 3,
                    "CDLEVENINGSTAR_Bull": 4,
                    "CDLEVENINGSTAR_Bear": 4,
                    # "CDLTASUKIGAP_Bull": 5,
                    # "CDLTASUKIGAP_Bear": 5,
                    # "CDLINVERTEDHAMMER_Bull": 6,
                    # "CDLINVERTEDHAMMER_Bear": 6,
                    # "CDLMATCHINGLOW_Bull": 7,
                    # "CDLMATCHINGLOW_Bear": 7,
                    # "CDLABANDONEDBABY_Bull": 8,
                    # "CDLABANDONEDBABY_Bear": 8,
                    # "CDLBREAKAWAY_Bull": 10,
                    # "CDLBREAKAWAY_Bear": 10,
                    # "CDLMORNINGSTAR_Bull": 12,
                    # "CDLMORNINGSTAR_Bear": 12,
                    }
    fig.update_layout(dragmode='zoom')
    best_candles = {k[3:].split('_')[0]: best_candles[k] for k in best_candles}
    locations = df_ohlcv[df_ohlcv['best_pattern'].isin(list(best_candles))]
    if not len(locations):
        print('found None')
    for idx, row in locations.iterrows():
        print(idx, row['best_pattern'], row['best_trend'])
        if row['best_trend'] > 0:
            fig.add_vline(idx, row=1, col=1, line_color='green', opacity=0.4)
        elif row['best_trend'] < 0:
            fig.add_vline(idx, row=1, col=1, line_color='red', opacity=0.4)
    fig.show()


if __name__ == '__main__':
    run_candle_idetification()
