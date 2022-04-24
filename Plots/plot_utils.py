from datetime import timedelta
import numpy as np
import pandas as pd

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # strftime
INTERVAL_UPDATE_SECONDS = 60
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
INTERVAL_CANDLE_LOOKBACK_LOAD_MULTIPLAYER = INTERVAL_CANDLE_LOOKBACK_DISPLAY_MULTIPLAYER * 3


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])


def fig_update_xylimits(fig, df_ohlc, resample):
    # x axis
    from DataProcessing.data_utils import adjust_plot_start_datetime
    start_display_dt = adjust_plot_start_datetime(resample, is_display=True)
    start_display_dt = max(df_ohlc.index[0], start_display_dt)
    print('display_date:', start_display_dt)
    time_now = df_ohlc.index[-1] + pd.to_timedelta(resample) * 5
    # yaxis
    df_ohlc_f = df_ohlc[df_ohlc.index > start_display_dt]
    min_std = df_ohlc_f['low'].std()
    min_val = df_ohlc_f['low'].min() - min_std
    max_std = df_ohlc_f['high'].std()
    max_val = df_ohlc_f['high'].max() + max_std

    # start_display_dt is half of the data loaded;  time_now takes 5 resample timedelta to have more room
    fig.update_xaxes(type="date", range=[start_display_dt, time_now])
    # Done: update only candle chart and not other figs
    # https://stackoverflow.com/questions/66842973/plotly-how-to-change-the-range-of-the-y-axis-of-a-subplot

    fig.update_layout(
        yaxis1=dict(range=[min_val, max_val]))  # may not be the best solution if using separate graphs
    # fig.update_yaxes(range=[min_val, max_val])
    # lock other axes to be fixed (TODO: should be the patterns)
    fig.update_layout(
        yaxis2=dict(fixedrange=True),  # range=[-100, 100]
        yaxis3=dict(fixedrange=True),
        yaxis4=dict(fixedrange=True),
    )


def fig_update_layout_combined_view(fig):
    fig.update_layout(xaxis_rangeslider_visible=False,
                      margin=dict(l=20, r=20, t=20, b=20),
                      hovermode='x unified',
                      # TODO: use dash in order to customise hover - https://community.plotly.com/t/how-to-customize-the-tooltip/9053/4
                      template="plotly_dark",
                      yaxis={"side": "right"},
                      #                       title=f'{coin} agg every {resample_keyword}, close price change %. ',
                      legend=dict(x=-0.07, y=1, font=dict(family="sans-serif", size=10, color="white"),
                                  traceorder="normal", ),
                      dragmode='pan'
                      )

    fig.update_layout(xaxis_showticklabels=True, xaxis2_showticklabels=False, )
    # fig.for_each_xaxis(lambda x: x.update(xaxis_showticklabels=True))
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
    # fig.update_layout(height=900, )
    # fig.update_layout(height=750, dragmode='pan')
    # fig.update_layout(uirevision='True') # does not work well when interval fires when zoomed in

    # Customizing Tick Label Formatting by Zoom Level
    # does not work quite well
    # fig.update_layout(xaxis_tickformatstops=[
    #     dict(dtickrange=[None, 60*1000], value="%H:%M:%S s"),
    #     dict(dtickrange=[60000, 3600000], value="%H:%M m"),
    #     dict(dtickrange=[3600000, 86400000], value="%H:%M"),  # hourly
    #     dict(dtickrange=[86400000, 604800000], value="%b %e"),  # daily
    #     dict(dtickrange=[604800000, "M1"], value="%e. %b w"),
    #     dict(dtickrange=["M1", "M12"], value="%b '%y M"),
    #     dict(dtickrange=["M12", None], value="%Y Y")])
