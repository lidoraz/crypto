from plotly.subplots import make_subplots
from cryptoUtils.crypto_utils import *
from LiveChart.plot_utils import *


# https://plotly.com/python/time-series/
# https://stackoverflow.com/questions/67459925/plotly-set-showgrid-false-for-all-subplots


def prepare_data(providers, start_datetime):
    price_provider = providers['price_provider']
    hourly_provider = providers['hourly_provider']
    df_prices = price_provider.serve()
    df_hourly = hourly_provider.serve()
    # filter
    allowed_timeframe_1 = df_prices.index.to_pydatetime() > start_datetime
    allowed_timeframe_2 = df_hourly.index.to_pydatetime() > start_datetime
    df_prices = df_prices[allowed_timeframe_1]
    df_hourly = df_hourly[allowed_timeframe_2]
    df_hourly = df_hourly[df_hourly.index.minute == 59]  # cutout only last mintue
    df_hourly = df_hourly.resample('1H', closed='right').ffill()
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


def add_moving_avgs(ohlc, col='close', show=True):
    if show:
        # add daily Averages
        fig.add_trace(get_MAD(ohlc, 7, col=col, color='orange'), row=1, col=1)
        fig.add_trace(get_MAD(ohlc, 25, col=col, color='purple'), row=1, col=1)
        fig.add_trace(get_MAD(ohlc, 99, col=col, color='cyan'), row=1, col=1)


def add_special_moving_avgs(ohlc, col='close', show=True):
    if show:
        # check fib and ema
        fig.add_trace(get_FibMAD(ohlc, 7, col=col, color='yellow'), row=1, col=1)
        fig.add_trace(get_EMA(ohlc, 7, col=col, color='orange'), row=1, col=1)


def get_updated_fig(providers, start_datetime, resample_keyword, coin):
    df_prices, df_hourly = prepare_data(providers, start_datetime)
    df_coin_ohlc = get_coin_ohlc(df_prices, coin, resample_keyword)

    # hourly.
    stats = get_coin_status(df_hourly, coin)
    print(f"{coin}:: {stats}")
    print(f"{coin} agg every {resample_keyword}, Price: {df_coin_ohlc.close.iloc[-1]}")

    n_rsi = 14
    df_coin_ohlc[f'rsi_{n_rsi}'] = calc_rsi(df_coin_ohlc, n_rsi)

    traces = [
        get_RSI_from_calucated(df_coin_ohlc[f'rsi_{n_rsi}'], n_rsi),
        #         get_pct_change_c(df_coin_ohlc),
        get_volume(coin, df_hourly, 'VOLUMEHOURTO'),
    ]
    fig = go.Figure(get_volume(coin, df_hourly, 'VOLUMEHOURTO'))
    # fig = go.Figure(get_candle_stick(df_coin_ohlc))
    # fig = make_subplots(rows=len(traces) + 1, cols=1,
    #                     row_heights=[5] + [1 for _ in traces],
    #                     #                         row_titles=['Candle','PctH%','Vol'],
    #                     shared_xaxes=True, )
    # fig.add_trace(get_candle_stick(df_coin_ohlc), row=1, col=1)

    # add_moving_avgs(df_coin_ohlc, show=False)
    # add_special_moving_avgs(df_coin_ohlc, show=False)

    # for idx, trace in enumerate(traces):
    #     fig.add_trace(trace, row=idx + 2, col=1)

    # add rsi traces:
    #         fig.add_trace(.add_vrect(x0=0.9, x1=2), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False,
                      yaxis={"side": "right"},
                      hovermode='y unified')
    # fig.update_layout(xaxis_rangeslider_visible=False,
    #                   margin=dict(l=20, r=20, t=20, b=20),
    #                   paper_bgcolor="LightSteelBlue",
    #                   #                       yaxis= {"side":"right"},
    #                   #                       title=f'{coin} agg every {resample_keyword}, close price change %. ',
    #                   legend=dict(x=-0.07, y=1, font=dict(family="sans-serif", size=10, color="black"),
    #                               traceorder="normal", )
    #                   )
    # fig.update_layout(xaxis_showticklabels=True, xaxis2_showticklabels=False)
    # #     fig.for_each_xaxis(lambda x: x.update(xaxis_showticklabels=True))
    # fig.for_each_yaxis(lambda x: x.update(side="right"))
    #
    # # https://plotly.com/python/hover-text-and-formatting/
    # fig.update_xaxes(showgrid=True, zeroline=False,
    #                  showspikes=True, spikemode='across', spikesnap='cursor', showline=True,
    #                  spikecolor="grey", spikethickness=1, spikedash='dash')
    fig.update_xaxes(showgrid=True, zeroline=False,
                     showspikes=True, spikemode='across', spikesnap='cursor', showline=True,
                     spikecolor="grey", spikethickness=1, spikedash='dash')
    fig.update_yaxes(showspikes=True, spikedash='dash', spikemode='across',
                     spikecolor="grey", spikesnap="cursor", spikethickness=1, side="right")
    # fig.update_layout(spikedistance=1000, hoverdistance=1000)  # enables crosshair on all

    # # Edit hoveroptions
    # # for ser in range(0, len(fig['data'])):
    # #     fig['data'][ser]['hoverinfo'] = 'all'
    return fig


if __name__ == '__main__':
    from cryptoUtils.data_columns import COINS, HOURLY_COLS
    from cryptoUtils.DataProvider import DataProvider

    data_path = os.path.join(os.getcwd(), 'resources')

    coin = 'ETH'
    resample = '15Min'

    price_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data'), cols=COINS)
    hourly_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data_hourly'),
                                   cols=HOURLY_COLS)
    providers = dict(price_provider=price_provider,
                     hourly_provider=hourly_provider)
    filter_date = get_graph_start_datetime(resample)
    fig = get_updated_fig(providers, filter_date, resample, coin)
    fig.show()
