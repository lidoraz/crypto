from datetime import datetime, timedelta
import pandas as pd

# TODO: combine functions for plots from crypto utils into here
UPDATE_INTERVAL_SECONDS = 20
START_DATA_DATE = '2022-03-26'  # '2022-04-02'
START_DATA_DATETIME = pd.to_datetime(START_DATA_DATE, utc=True)
INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER = 1  # this will alter the display, also differs for how much data is loaded
INTERVAL_CANDLE_LOOKBACK_TABLE = {
    '2Min': timedelta(hours=6),
    # '3Min': timedelta(hours=10),
    '5Min': timedelta(hours=18),
    '15Min': timedelta(days=2),
    '1H': timedelta(days=8),
    '4H': timedelta(days=30),
    '12H': timedelta(days=30 * 3),
    '1D': timedelta(days=30 * 6)
}
INTERVAL_CANDLE_LOOKBACK_LOAD_MULTIPLAYER = 2 * INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER


# TODO: rename this function
def get_graph_start_datetime(interval_length: str, is_display=False, tz_isr=True):
    time_now = pd.to_datetime(datetime.utcnow(), utc=True)
    start_datetime = time_now.tz_convert('Israel') if tz_isr else time_now

    if interval_length in INTERVAL_CANDLE_LOOKBACK_TABLE:
        if is_display:
            delta = INTERVAL_CANDLE_LOOKBACK_TABLE[interval_length] * INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER
        else:
            delta = INTERVAL_CANDLE_LOOKBACK_TABLE[interval_length] * INTERVAL_CANDLE_LOOKBACK_LOAD_MULTIPLAYER
        filter_datetime = (start_datetime - delta)
        if filter_datetime > start_datetime:
            filter_datetime = start_datetime
        # print(f'filter_datetime = {filter_datetime}')
    else:
        filter_datetime = START_DATA_DATE
    return filter_datetime


import numpy as np

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])


def calc_rsi(df_coin, n, col='close'):
    if n >= len(df_coin):  # fail safe in case of an error
        n = len(df_coin) - 1

    # https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe
    def rma(x, n, y0):
        a = (n - 1) / n
        ak = a ** np.arange(len(x) - 1, -1, -1)
        return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a ** np.arange(1, len(x) + 1)]

    df = df_coin.copy()
    df['change'] = df[col].diff()
    df['gain'] = df.change.mask(df.change < 0, 0.0)
    df['loss'] = -df.change.mask(df.change > 0, -0.0)
    df['avg_gain'] = rma(df.gain[n + 1:].to_numpy(), n, np.nansum(df.gain.to_numpy()[:n + 1]) / n)
    df['avg_loss'] = rma(df.loss[n + 1:].to_numpy(), n, np.nansum(df.loss.to_numpy()[:n + 1]) / n)
    df['rs'] = df.avg_gain / df.avg_loss
    df['rsi_n'] = 100 - (100 / (1 + df.rs))
    return df['rsi_n']


def fig_update_xylimits(fig, df_ohlc, resample):
    # x axis
    start_display_dt = get_graph_start_datetime(resample, is_display=True)
    start_display_dt = max(df_ohlc.index[0], start_display_dt)
    print('display date:', start_display_dt)
    time_now = df_ohlc.index[-1] + pd.to_timedelta(resample) * 5
    # yaxis
    df_ohlc_f = df_ohlc[df_ohlc.index > start_display_dt]
    min_std = df_ohlc_f['low'].std()
    min_val = df_ohlc_f['low'].min() - min_std
    max_std = df_ohlc_f['high'].std()
    max_val = df_ohlc_f['high'].max() + max_std

    # start_display_dt is half of the data loaded;  time_now takes 5 resample timedelta to have more room
    fig.update_xaxes(range=[start_display_dt, time_now])
    # Done: update only candle chart and not other figs
    # https://stackoverflow.com/questions/66842973/plotly-how-to-change-the-range-of-the-y-axis-of-a-subplot
    fig.update_layout(
        yaxis1=dict(range=[min_val, max_val]))  # may not be the best solution if using separate graphs
    # fig.update_yaxes(range=[min_val, max_val])


def fig_update_layout_combined_view(fig):
    fig.update_layout(xaxis_rangeslider_visible=False,
                      margin=dict(l=20, r=20, t=20, b=20),
                      hovermode='x unified',
                      # TODO: use dash in order to customise hover - https://community.plotly.com/t/how-to-customize-the-tooltip/9053/4
                      template="plotly_dark",
                      yaxis={"side": "right"},
                      #                       title=f'{coin} agg every {resample_keyword}, close price change %. ',
                      legend=dict(x=-0.07, y=1, font=dict(family="sans-serif", size=10, color="white"),
                                  traceorder="normal", )
                      )

    fig.update_layout(xaxis_showticklabels=True, xaxis2_showticklabels=False)
    #     fig.for_each_xaxis(lambda x: x.update(xaxis_showticklabels=True))
    fig.for_each_yaxis(lambda x: x.update(side="right"))
    fig.update_xaxes(showgrid=True, zeroline=False,  # rangeslider_visible=False, showticklabels=False,
                     showspikes=True, spikemode='across', spikesnap='cursor', showline=True,
                     spikecolor="grey", spikethickness=1, spikedash='dash')
    fig.update_yaxes(showspikes=True, spikedash='dash', spikemode='across',  # fixedrange=True,
                     spikecolor="grey", spikesnap="cursor", spikethickness=1)
    fig.update_layout(spikedistance=1000, hoverdistance=1000)  # enables crosshair on all

    # fig.update_xaxes(autorange=False)
    # fig.update_yaxes(autorange=False)
    # fig.update_xaxes(fixedrange=True)  # does not fix the problem. it limits x from both sides, need to limit only 1 side.
    fig.update_layout(height=700, dragmode='pan')
