import plotly.graph_objects as go
from DataProcessing.data_utils import *
# from Plots.traces import get_pattern_fig
from Indicators import CandleIdentification

coin = 'ETH'
interval = '4H'

filter_datetime = adjust_plot_start_datetime(interval)
providers = get_data_providers()
df_prices, df_hourly = prepare_data(providers, filter_datetime)
df = get_coin_ohlc(df_prices, coin, interval)

ind = CandleIdentification()
ind.calc(df)
fig = go.Figure()
ind.plot(fig)
fig.show()
