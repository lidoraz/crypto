from plotly.subplots import make_subplots

from .add_to_fig import add_moving_avgs, add_special_moving_avgs
from .plot_utils import *

# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots
from .traces import get_candle_stick, get_pct_change_c, get_volume, get_RSI_from_calucated


def prepare_data(providers, start_datetime):
    print('load date:', start_datetime)
    price_provider = providers['price_provider']
    hourly_provider = providers['hourly_provider']
    df_prices = price_provider.serve()
    df_hourly = hourly_provider.serve()
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


# TODO: since below date data became refreshed every 15 min
# TODO: add here is there could be a problem if data is not refreshed every 15 min (can be in rare coins)
def extract_volume(df_hourly, coin, resample_keyword, cols=('VOLUMEHOUR', 'VOLUMEHOURTO')):
    def inverse_cumsum(
            x):  # https://stackoverflow.com/questions/38666924/what-is-the-inverse-of-the-numpy-cumsum-function
        return np.diff(x, prepend=0)

    if 'Min' in resample_keyword and int(resample_keyword.split('Min')[0]) < 15:
        interval_hourly = '15Min'
    else:
        interval_hourly = resample_keyword
    coin_cols = [f'{coin}_{col}' for col in cols]
    df_hourly = df_hourly[df_hourly.index > pd.to_datetime('2022-04-09', utc=True).tz_convert('Israel')]

    grps = df_hourly[coin_cols].groupby(df_hourly.index.floor('h'))
    df_volume_by_interval = grps.transform(inverse_cumsum)  # apply function column-by-column to the grouped
    df_volume_by_interval = df_volume_by_interval.resample(interval_hourly, closed='right').ffill()
    return df_volume_by_interval[coin_cols[0]], df_volume_by_interval[coin_cols[1]]


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
    traces = [
        get_RSI_from_calucated(calculated_rsi, n_rsi),
        get_pct_change_c(df_ohlc['close'], resample='1H'),
        # TODO: add here maybe option to take 2 times high granularity for 4 hourly change for 15 min chart.
        get_volume(volumehourto)]

    fig = make_subplots(rows=len(traces) + 1, cols=1,
                        row_heights=[8] + [1 for _ in traces],
                        shared_xaxes=True)
    fig.add_trace(get_candle_stick(df_ohlc), row=1, col=1)

    add_moving_avgs(fig, df_ohlc)
    # add_special_moving_avgs(fig, df_coin_ohlc, show=False)

    for idx, trace in enumerate(traces):
        fig.add_trace(trace, row=idx + 2, col=1)

    fig_update_layout_combined_view(fig)
    fig_update_xylimits(fig, df_ohlc, resample_keyword)

    return fig
