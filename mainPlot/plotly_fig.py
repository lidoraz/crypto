from plotly.subplots import make_subplots
from cryptoUtils.crypto_utils import *
from mainPlot.plot_utils import fig_update_layout_combined_view, get_graph_start_datetime


# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots


def prepare_data(providers, start_datetime):
    price_provider = providers['price_provider']
    hourly_provider = providers['hourly_provider']
    df_prices = price_provider.serve()
    df_hourly = hourly_provider.serve()
    # filter #TODO: CASE1
    print('load date:', start_datetime)
    df_prices = df_prices[df_prices.index.to_pydatetime() > start_datetime]
    df_hourly = df_hourly[df_hourly.index.to_pydatetime() > start_datetime]
    # is_ok_time_diff = len(df_prices[list(df_prices.reset_index()['timestamp'].diff().dt.total_seconds() > 120)]) == 0
    # assert is_ok_time_diff, 'There are instances with larger time diff'
    return df_prices, df_hourly


def get_coin_ohlc(df, coin, resample_keyword):
    return df[coin].resample(resample_keyword, closed='right').ohlc()


def get_coin_status(df_hourly, coin):
    cols = ['VOLUMEDAY', 'CHANGEPCT24HOUR', 'VOLUME24HOURTO']
    coin_cols = [f'{coin}_{col}' for col in cols]
    coin_stats = df_hourly[coin_cols].iloc[-1]  # df_hourly.index[-1]
    coin_stats = coin_stats.apply(human_format)
    stats = {k: v for k, v in zip(cols, coin_stats)}
    return stats


def extract_volume(df_hourly, coin, interval_hourly, cols=('VOLUMEHOUR', 'VOLUMEHOURTO')):
    coin_cols = [f'{coin}_{col}' for col in cols]
    # TODO: since below date data became refreshed every 15 min
    # TODO: add here is there could be a problem if data is not refreshed every 15 min (can be in rare coins)
    df_hourly = df_hourly[df_hourly.index > pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')]
    grps = df_hourly[coin_cols].groupby(df_hourly.index.floor('h'))
    inverse_cumsum = lambda x: np.diff(x,
                                       prepend=0)  # https://stackoverflow.com/questions/38666924/what-is-the-inverse-of-the-numpy-cumsum-function
    df_volume_by_interval = grps.transform(inverse_cumsum)  # apply function column-by-column to the grouped
    df_volume_by_interval = df_volume_by_interval.resample(interval_hourly, closed='right').ffill()
    return df_volume_by_interval[coin_cols[0]], df_volume_by_interval[coin_cols[1]]


def add_moving_avgs(fig, ohlc, col='close', show=True):
    if show:
        # add daily Averages
        fig.add_trace(get_MAD(ohlc, 7, col=col, color='orange'), row=1, col=1)
        fig.add_trace(get_MAD(ohlc, 25, col=col, color='purple'), row=1, col=1)
        fig.add_trace(get_MAD(ohlc, 99, col=col, color='cyan'), row=1, col=1)


def add_special_moving_avgs(fig, ohlc, col='close', show=True):
    if show:
        # check fib and ema
        fig.add_trace(get_FibMAD(ohlc, 7, col=col, color='yellow'), row=1, col=1)
        fig.add_trace(get_EMA(ohlc, 7, col=col, color='orange'), row=1, col=1)


def get_updated_fig(providers, start_datetime, resample_keyword, coin):
    df_prices, df_hourly = prepare_data(providers, start_datetime)
    if 'Min' in resample_keyword and int(resample_keyword.split('Min')[0]) < 15:
        interval_hourly = '15Min'
    else:
        interval_hourly = resample_keyword
    # df_hourly = df_hourly[df_hourly.index.minute == 59]  # cutout only last mintue
    # df_hourly = df_hourly.resample(interval_hour, closed='right').ffill()
    volume_hour, volumehourto = extract_volume(df_hourly, coin, interval_hourly)
    df_coin_ohlc = get_coin_ohlc(df_prices, coin, resample_keyword)

    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats}")
    print(f"{coin} agg every {resample_keyword}, Price: {df_coin_ohlc.close.iloc[-1]}")

    n_rsi = 14
    # n_rsis = [7, 14, 30]
    df_coin_ohlc[f'rsi_{n_rsi}'] = calc_rsi(df_coin_ohlc, n_rsi)

    traces = [
        get_RSI_from_calucated(df_coin_ohlc[f'rsi_{n_rsi}'], n_rsi),
        get_pct_change_c(df_coin_ohlc),
        get_volume(volumehourto),
    ]

    fig = make_subplots(rows=len(traces) + 1, cols=1,
                        row_heights=[8] + [1 for _ in traces],
                        #                         row_titles=['Candle','PctH%','Vol'],
                        shared_xaxes=True)
    fig.add_trace(get_candle_stick(df_coin_ohlc), row=1, col=1)

    add_moving_avgs(fig, df_coin_ohlc, show=True)
    add_special_moving_avgs(fig, df_coin_ohlc, show=False)

    for idx, trace in enumerate(traces):
        fig.add_trace(trace, row=idx + 2, col=1)
    fig_update_layout_combined_view(fig)

    # limit: #TODO: need to keep data in order to calcuate moving averages.. but limit the ranges here.
    # TODO: CASE1
    # time_now = df_coin_ohlc.index[-1]
    # time_now = pd.to_datetime(datetime.utcnow(), utc=3).tz_convert('Israel')
    # print(start_datetime, time_now)
    # fig.update_xaxes(range=[start_datetime, time_now])

    def set_fig_limits(fig, df_ohlc, resample):
        # x axis
        start_display_dt = get_graph_start_datetime(resample, is_display=True)
        start_display_dt = max(df_ohlc.index[0], start_display_dt)
        print('display date:', start_display_dt)
        time_now = df_ohlc.index[-1] + pd.to_timedelta(resample) * 5

        # yaxis
        df_ohlc_f = df_coin_ohlc[df_coin_ohlc.index > start_display_dt]
        min_std = df_ohlc_f['low'].std()
        min_val = df_ohlc_f['low'].min() - min_std
        max_std = df_ohlc_f['high'].std()
        max_val = df_ohlc_f['high'].max() + max_std

        # start_display_dt is half of the data loaded
        # time_now takes 5 resample timedelta to have more room
        fig.update_xaxes(range=[start_display_dt, time_now])
        # Done: update only candle chart and not other figs
        # https://stackoverflow.com/questions/66842973/plotly-how-to-change-the-range-of-the-y-axis-of-a-subplot
        fig.update_layout(
            yaxis1=dict(range=[min_val, max_val]))  # may not be the best solution if using separate graphs
        # fig.update_yaxes(range=[min_val, max_val])

    set_fig_limits(fig, df_coin_ohlc, resample_keyword)
    fig.update_layout(height=685, dragmode='pan')
    return fig
