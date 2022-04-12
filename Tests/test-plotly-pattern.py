from AdvancedAnalytics.PatternDetection.identify_candlestick import recognize_candles
from DataProcessing.data_utils import *

coin = 'ETH'
interval = '4H'

filter_datetime = adjust_plot_start_datetime(interval)
providers = get_data_providers()
df_prices, df_hourly = prepare_data(providers, filter_datetime)
df = get_coin_ohlc(df_prices, coin, interval)

import plotly.graph_objects as go

# import plotly.express as px

# pattern_value > 0
fig = go.Figure(get_pattern_fig(df))
fig.show()

# ADD THIS AS TRACE
