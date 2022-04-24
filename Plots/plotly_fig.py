from plotly.subplots import make_subplots
from DataProcessing.data_utils import prepare_data, extract_volume, get_coin_status
from .add_to_fig import add_moving_avgs, add_special_moving_avgs
from .plot_utils import *
from .traces import *
from Indicators import *


# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots


def get_updated_fig(providers, start_datetime, resample_keyword, coin, lookahead=25, xy_limit=True):
    df_prices, df_hourly = prepare_data(providers, start_datetime)
    volume_hour, volume_hourto = extract_volume(df_hourly, coin, resample_keyword)
    # traces = ['candle', 'pattern', 'rsi', 'volume']

    sub_plots = [None,  # candle
                 CandleIdentification(plot_loc=2),
                 RSI(lookahead, plot_loc=3),
                 # MACD(plot_loc=3),
                 None
                 ]

    row_heights = [len(sub_plots) * 2] + [1 for _ in sub_plots]  # relative height of main frame compared to all traces
    # row_heights = [6, 3, 1, 1]
    fig = make_subplots(rows=len(sub_plots) + 1, cols=1,
                        row_heights=row_heights,
                        vertical_spacing=0.05,
                        # specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                        shared_xaxes=True)
    ind_candle = CandleStick(resample_keyword, plot_loc=1)
    df_ohlc = ind_candle.calc(df_prices[coin])
    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats} :: agg every {resample_keyword}, Price: {df_ohlc.close.iloc[-1]}")
    ind_candle.plot(fig)

    # ind_bb = MACD(plot_loc=3)
    # ind_bb.calc(df_ohlc['close'])
    # ind_bb.plot(fig)
    main_plot_indicators = [
        # SMA(lookahead=7, plot_loc=1, color='orange'),
        # SMA(lookahead=25, plot_loc=1, color='purple'),
        # SMA(lookahead=99, plot_loc=1, color='cyan'),
        # FibMA(14, color='Pink'),
        # EMA(14, color='Teal'),
        BollingerBands(lookahead, 2, visible=True, plot_loc=1),
        SupportResistanceLines(geometric_spacing=False, plot_loc=1)]

    for ind in main_plot_indicators:
        ind.calc(df_ohlc)
        ind.plot(fig)

    for sub_plot in sub_plots:
        if sub_plot:
            _ = sub_plot.calc(df_ohlc)
            fig = sub_plot.plot(fig)
    fig.add_trace(get_volume(volume_hourto, df_ohlc), row=4, col=1)
    fig_update_layout_combined_view(fig)
    if xy_limit:
        fig_update_xylimits(fig, df_ohlc, resample_keyword)

    return fig
