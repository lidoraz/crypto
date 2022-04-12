# brew install ta-lib
# python3 -m pip install TA-Lib
import talib

from PatternDetection.identify_candlestick import recognize_candles
from DataProcessing.data_utils import *

candle_names = talib.get_function_groups()['Pattern Recognition']

print(candle_names)

coin = 'ETH'
interval = '1H'

filter_datetime = adjust_plot_start_datetime(interval)
providers = get_data_providers()
df_prices, df_hourly = prepare_data(providers, filter_datetime)
df = get_coin_ohlc(df_prices, coin, interval)
# create columns for each pattern
# for candle in candle_names:
#     # below is same as;
#     # df["CDL3LINESTRIKE"] = talib.CDL3LINESTRIKE(op, hi, lo, cl)
#     df[candle] = getattr(talib, candle)(df['open'], df['high'], df['low'], df['close'])

# from .PatternDetection.identify_candlesticks import recognize_candlestick

df_patterns = recognize_candles(df)

# def extract_trend(pattern_name):
#     if "Bull" in pattern_name:
#         return 1
#     elif "Bear" in pattern_name:
#         return -1

# df['trend'] = df['candlestick_pattern'].apply(extract_trend)

print(coin)
print(interval)
# print(df_patterns['ranking'].value_counts().sort_index())
print(df_patterns[df_patterns['ranking'] < 10])
# print(df[df['candlestick_match_count'] >= 4]['candlestick_pattern'])

# print(df[~df['trend'].isnull()]['candlestick_pattern'])
# print(df['candlestick_match_count'].value_counts())
