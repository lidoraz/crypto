from plotly.subplots import make_subplots
from DataProcessing.data_utils import prepare_data, extract_volume, get_coin_status, get_coin_ohlc
from .add_to_fig import add_moving_avgs
from .plot_utils import *
from .traces import *
from Plots.Indicators import SMA, RSI, MACD, BollingerBands
# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots


def get_updated_fig(providers, start_datetime, resample_keyword, coin, lookahead=25, xy_limit=True):
    df_prices, df_hourly = prepare_data(providers, start_datetime)
    volume_hour, volume_hourto = extract_volume(df_hourly, coin, resample_keyword)
    df_ohlc = get_coin_ohlc(df_prices, coin, resample_keyword)

    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats} :: agg every {resample_keyword}, Price: {df_ohlc.close.iloc[-1]}")
    # n_rsi = 30
    # add_rsi_vlines = True
    # calculated_rsi = calc_rsi(df_ohlc, n_rsi)
    # traces = [
    #     ('pattern', get_pattern_fig(df_ohlc)),
    #     ('volume', get_volume(volume_hourto, df_ohlc)),
    #     # ('RSI', get_RSI_from_calucated(calculated_rsi, n_rsi)),
    #     # ('PCT_CHG', get_fig_pct_change_c(df_ohlc['close'], resample=resample_keyword)),  # resample='1H'
    # ]
    traces = ['candle', 'pattern', 'rsi', 'volume']

    # change_pct_resample =  # TODO: maybe add here, add here maybe option to take 2 times high granularity for 4 hourly change for 15 min chart.

    row_heights = [len(traces) * 2] + [1 for _ in traces]  # relative height of main frame compared to all traces
    # row_heights = [6, 3, 1, 1]
    fig = make_subplots(rows=len(traces) + 1, cols=1,
                        row_heights=row_heights,
                        vertical_spacing=0.05,
                        # specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                        shared_xaxes=True)

    fig.add_trace(get_candle_stick(df_ohlc), row=1, col=1)
    fig.add_trace(get_pattern_fig(df_ohlc), row=2, col=1)

    fig.add_trace(get_volume(volume_hourto, df_ohlc), row=4, col=1)

    add_moving_avgs(fig, df_ohlc)

    # ind_bb = MACD()
    # ind_bb.calc(df_ohlc['close'])
    # ind_bb.plot(fig, loc=(3, 1))
    ind_rsi = RSI(lookahead)
    ind_rsi.calc(df_ohlc['close'])
    ind_rsi.plot(fig, loc=(3, 1))

    ind_bb = BollingerBands(lookahead, 2, visible=True)
    ind_bb.calc(df_ohlc['close'])
    ind_bb.plot(fig, loc=(1, 1))
    # add_bollinger_bands(fig, df_ohlc)

    # add_special_moving_avgs(fig, df_ohlc)

    # fig.add_trace(traces[0], row=1, col=1)

    # for idx, tup in enumerate(traces):
    #     name, trace = tup
    #     curr_row = idx + 2
    #     fig.add_trace(trace, row=curr_row, col=1)
    #     if name == 'RSI' and add_rsi_vlines:  # add RSI LINES
    #         fig.add_hline(y=70, row=curr_row, col=1, line_width=1, line_color='green', line_dash="dash")
    #         fig.add_hline(y=30, row=curr_row, col=1, line_width=1, line_color='red', line_dash="dash")

    fig_update_layout_combined_view(fig)
    if xy_limit:
        fig_update_xylimits(fig, df_ohlc, resample_keyword)

    return fig
