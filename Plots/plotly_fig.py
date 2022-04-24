from plotly.subplots import make_subplots
from DataProcessing.data_utils import get_coin_status, get_crypto_olhcv
from .plot_utils import *
from Indicators import *


def get_updated_fig(df_ohlcv, lookahead=14, xy_limit=True):
    interval = df_ohlcv.attrs['interval']
    sub_plots = [None,  # candle
                 CandleIdentification(normalize_detected_patterns=False, plot_loc=2),
                 RSI(lookahead, plot_loc=3),
                 # MACD(plot_loc=3),
                 Volume(plot_loc=4)
                 ]

    row_heights = [len(sub_plots) * 2] + [1 for _ in sub_plots]  # relative height of main frame compared to all traces
    # row_heights = [6, 3, 1, 1]
    fig = make_subplots(rows=len(sub_plots) + 1, cols=1,
                        row_heights=row_heights,
                        # vertical_spacing=0.05,
                        # specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                        shared_xaxes=True)

    ind_candle = CandleStick(interval, ohlc=df_ohlcv, plot_loc=1)
    ind_candle.plot(fig)

    main_plot_indicators = [
        # SMA(lookahead=7, plot_loc=1, color='orange'),
        # SMA(lookahead=25, plot_loc=1, color='purple'),
        # SMA(lookahead=99, plot_loc=1, color='cyan'),
        # FibMA(14, color='Pink'),
        # EMA(14, color='Teal'),
        BollingerBands(lookahead, 2, visible=True, plot_loc=1),
        SupportResistanceLines(geometric_spacing=False, plot_loc=1)]

    for ind in main_plot_indicators:
        ind.calc(df_ohlcv)
        ind.plot(fig)

    for sub_plot in sub_plots:
        if sub_plot:
            _ = sub_plot.calc(df_ohlcv)
            fig = sub_plot.plot(fig)
    fig_update_layout_combined_view(fig)
    if xy_limit:
        fig_update_xylimits(fig, df_ohlcv, interval)

    return fig

# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots
