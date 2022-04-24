import plotly.graph_objects as go
from Crypto.DataProcessing.data_utils import *
# from Plots.traces import get_pattern_fig
from Indicators import CandleIdentification, CandleStick

coin = 'ETH'
interval = '4H'

filter_datetime = adjust_plot_start_datetime(interval)
providers = get_data_providers()
df_prices, df_hourly = prepare_data(providers, filter_datetime)
df = CandleStick(interval).calc(df_prices[coin])

ind = CandleIdentification()
ind.calc(df)
fig = go.Figure()
ind.plot(fig)
fig.show()
