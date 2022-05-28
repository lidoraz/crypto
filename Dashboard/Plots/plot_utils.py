from datetime import timedelta
import numpy as np
import pandas as pd

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # strftime
INTERVAL_UPDATE_SECONDS = 30  # 5
# 1 -> not limit , 0.5 -> display half data
INTERVAL_CANDLE_LOOKBACK_DISPLAY_DIVIDED = 0.4  # start display from this relative value (pct)
# loading multiplier
LOAD_DATA_MUL = 4  # 3.5 # 40 # TODO: this needs to be fixed, as a parameter for dashboard not a constant
INTERVAL_CANDLE_LOOKBACK_TABLE = {
    '1T': timedelta(hours=0.5 * LOAD_DATA_MUL),
    '5T': timedelta(hours=5 * LOAD_DATA_MUL),
    '15T': timedelta(hours=15 * LOAD_DATA_MUL),
    '1H': timedelta(hours=60 * LOAD_DATA_MUL),
    '4H': timedelta(hours=60 * 4 * LOAD_DATA_MUL),
    '12H': timedelta(hours=60 * 4 * 3 * LOAD_DATA_MUL),
    '1D': timedelta(hours=60 * 4 * 6 * LOAD_DATA_MUL)
}


def fig_update_xylimits(fig, df_ohlc, resample, ylimit=False):
    # x axis
    start_data_dt = df_ohlc.index[0]
    last_data_dt = df_ohlc.index[-1]
    # take percent of display.
    start_display_idx = int(len(df_ohlc) * INTERVAL_CANDLE_LOOKBACK_DISPLAY_DIVIDED)
    start_display_dt = df_ohlc.index[start_display_idx]
    print(f'start_data_dt={start_data_dt}, last_data_dt={last_data_dt}, start_display_dt={start_display_dt}')

    # yaxis
    df_ohlc_f = df_ohlc[df_ohlc.index > start_display_dt]
    if ylimit:
        min_std = df_ohlc_f['low'].std()
        min_val = df_ohlc_f['low'].min() - min_std
        max_std = df_ohlc_f['high'].std()
        max_val = df_ohlc_f['high'].max() + max_std
        # may not be the best solution if using separate graphs
        fig.update_layout(yaxis1=dict(range=[min_val, max_val]))

    last_display_dt = last_data_dt + pd.to_timedelta(resample) * 3
    fig.update_xaxes(type="date", range=[start_display_dt, last_display_dt])
    # Done: update only candle chart and not other figs
    # https://stackoverflow.com/questions/66842973/plotly-how-to-change-the-range-of-the-y-axis-of-a-subplot

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
                      legend=dict(x=-0.07, y=1, font=dict(family="sans-serif", size=10, color="white"),
                                  traceorder="normal", ),
                      dragmode='pan')
    fig.for_each_xaxis(lambda x: x.update(showticklabels=False))
    fig.update_layout(xaxis_showticklabels=True)
    fig.for_each_yaxis(lambda x: x.update(side="right"))
    spike_params = dict(showspikes=True, spikedash='dash', spikemode='across', spikecolor="grey", spikesnap="cursor",
                        spikethickness=0.5)
    fig.update_xaxes(**spike_params)  # rangeslider_visible=False, showticklabels=False, showgrid=True, zeroline=False,
    fig.update_yaxes(**spike_params)  # fixedrange=True,
