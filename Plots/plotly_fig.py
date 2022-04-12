from plotly.subplots import make_subplots
from DataProcessing.data_utils import prepare_data, extract_volume, get_coin_status, get_coin_ohlc
from .add_to_fig import add_moving_avgs
from .plot_utils import *
from .traces import *

# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots


def get_updated_fig(providers, start_datetime, resample_keyword, coin):
    df_prices, df_hourly = prepare_data(providers, start_datetime)

    # TODO workout this
    # df_hourly = df_hourly[df_hourly.index.minute == 59]  # cutout only last mintue
    # df_hourly = df_hourly.resample(interval_hour, closed='right').ffill()
    volume_hour, volumehourto = extract_volume(df_hourly, coin, resample_keyword)
    df_ohlc = get_coin_ohlc(df_prices, coin, resample_keyword)

    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats} :: agg every {resample_keyword}, Price: {df_ohlc.close.iloc[-1]}")
    n_rsi = 14
    calculated_rsi = calc_rsi(df_ohlc, n_rsi)
    # change_pct_resample =  # TODO: maybe add here
    traces = [
        # get_pattern_fig(df_ohlc),
        get_RSI_from_calucated(calculated_rsi, n_rsi),
        get_fig_pct_change_c(df_ohlc['close'], resample=resample_keyword),  # resample='1H'
        # TODO: add here maybe option to take 2 times high granularity for 4 hourly change for 15 min chart.
        get_volume(volumehourto)
    ]

    row_heights = [len(traces) * 3] + [1 for _ in traces]  # relative height of main frame compared to all traces
    # row_heights = [2] + [1 for _ in traces]

    fig = make_subplots(rows=len(traces) + 1, cols=1,
                        row_heights=row_heights,
                        shared_xaxes=True)
    fig.add_trace(get_candle_stick(df_ohlc), row=1, col=1)

    add_moving_avgs(fig, df_ohlc)
    # add_special_moving_avgs(fig, df_coin_ohlc, show=False)

    for idx, trace in enumerate(traces):
        fig.add_trace(trace, row=idx + 2, col=1)

    fig_update_layout_combined_view(fig)
    fig_update_xylimits(fig, df_ohlc, resample_keyword)

    return fig
