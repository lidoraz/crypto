from plotly.subplots import make_subplots
from .plot_utils import *
from Indicators import *


def get_updated_fig(df_ohlcv, lookahead=14, support_lookback_ratio=None, support_index=-1, xy_limit=True,
                    show_legend=True):
    interval = df_ohlcv.attrs['interval']
    coin = df_ohlcv.attrs['symbol']
    ind_candle = CandleStick(interval, ohlc=df_ohlcv, plot_loc=1)

    sub_plots = [
        Volume(),
        # CandleIdentification(normalize_detected_patterns=False),
        RSI(lookahead),
        # StochRSI(lookahead, 5)
        # MACD(),
    ]
    for idx, s_plot in enumerate(sub_plots):
        s_plot.plot_loc = (idx + 2, 1)

    # relative height of main frame compared to all traces
    row_heights = [len(sub_plots) * 2] + [1 for _ in sub_plots]

    fig = make_subplots(rows=len(sub_plots) + 1, cols=1,
                        row_heights=row_heights,  # [6, 3, 1, 1]
                        vertical_spacing=0.02,  # 0.04,
                        # specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                        shared_xaxes=True)
    ind_candle.plot(fig)

    main_plot_indicators = [
        SMA(lookahead=7, plot_loc=1, color='orange'),
        SMA(lookahead=25, plot_loc=1, color='purple'),
        SMA(lookahead=99, plot_loc=1, color='cyan'),
        # FibMA(14, color='Pink'),
        # EMA(14, color='Teal'),
        BollingerBands(lookahead, 2, visible=False, plot_loc=1),
        SupportResistanceLines2(lookback_ratio=support_lookback_ratio, plot_index=support_index, plot_loc=1)
    ]
    # SupportResistanceLines(upto_lookahead=720, n_lookaheads=5, geometric_spacing=False, plot_loc=1)]

    for ind in main_plot_indicators:
        _ = ind.calc(df_ohlcv)
        ind.plot(fig)
    for sub_plot in sub_plots:
        _ = sub_plot.calc(df_ohlcv)
        fig = sub_plot.plot(fig)

    fig_update_layout_combined_view(fig)
    if xy_limit:
        fig_update_xylimits(fig, df_ohlcv, interval)
        fig.update_layout(showlegend=show_legend)
        # Don't change location when interval triggers:
        # does not work well when interval fires when zoomed in
        fig.update_layout(uirevision=f'{coin}{interval}')
    return fig

# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots
