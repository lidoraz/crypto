from plotly.subplots import make_subplots
from .plot_utils import *
from Indicators import *


def get_generic_plots():
    sub_plots = [
        Volume(),
        CandleIdentification(normalize_detected_patterns=False),
        # RSI(14),
        # StochRSI(lookahead, 5),
        # MACD(lookahead_short=12, lookahead_long=26, lookahead_signal=9),
    ]
    main_plot_indicators = [
        SMA(lookback=7, plot_loc=1, color='orange'),
        SMA(lookback=25, plot_loc=1, color='purple'),
        SMA(lookback=99, plot_loc=1, color='cyan'),
        # EMA(lookahead=99, plot_loc=1, color='cyan'),
        # FibMA(14, color='Pink'),
        # EMA(14, color='Teal'),
        BollingerBands(20, 2, visible=False, plot_loc=1),
        SupportResistanceLines2(lookback_length=None, plot_index=-1, plot_loc=1)
    ]
    return main_plot_indicators, sub_plots


def get_updated_fig(df_ohlcv, main_plot_ind=(), sub_plots=(), xy_limit=True, show_legend=True, with_data=False,
                    calc_ind=True):
    if not len(main_plot_ind) and not len(sub_plots):
        main_plot_ind, sub_plots = get_generic_plots()

    interval = df_ohlcv.attrs['interval']
    coin = df_ohlcv.attrs['symbol']
    ind_candle = CandleStick(interval, ohlc=df_ohlcv, plot_loc=1)

    for idx, s_plot in enumerate(sub_plots):
        s_plot.plot_loc = (idx + 2, 1)

    # relative height of main frame compared to all traces
    row_heights = [len(sub_plots) * 3] + [1 for _ in sub_plots]

    fig = make_subplots(rows=len(sub_plots) + 1, cols=1,
                        row_heights=row_heights,  # [6, 3, 1, 1]
                        vertical_spacing=0.02,  # 0.04,
                        # specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                        shared_xaxes=True)
    ind_candle.plot(df_ohlcv, fig)

    if calc_ind:
        for ind in main_plot_ind + sub_plots:
            df_ohlcv = df_ohlcv.join(ind.calc(df_ohlcv))

    df_ohlcv = df_ohlcv.dropna()
    for ind in main_plot_ind + sub_plots:
        fig = ind.plot(df_ohlcv, fig)

    fig_update_layout_combined_view(fig)
    if xy_limit:
        fig_update_xylimits(fig, df_ohlcv, interval)
        fig.update_layout(showlegend=show_legend)
        # Don't change location when interval triggers:
        # does not work well when interval fires when zoomed in
        fig.update_layout(uirevision=f'{coin}{interval}')

    if with_data:
        return fig, df_ohlcv
    else:
        return fig

# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots
