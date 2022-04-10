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
    #
    # # https://plotly.com/python/hover-text-and-formatting/
    fig.update_xaxes(showgrid=True, zeroline=False,  # rangeslider_visible=False, showticklabels=False,
                     showspikes=True, spikemode='across', spikesnap='cursor', showline=True,
                     spikecolor="grey", spikethickness=1, spikedash='dash')
    fig.update_yaxes(showspikes=True, spikedash='dash', spikemode='across',
                     spikecolor="grey", spikesnap="cursor", spikethickness=1)
    fig.update_layout(spikedistance=1000, hoverdistance=1000)  # enables crosshair on all

    # fig.update_layout(dragmode=False) # disable drag on axes
