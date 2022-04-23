# %%time
# def is_time_updated(time_now, treshold_seconds=90):
#     return (datetime.utcnow() - time_now.tz_convert(None)).total_seconds() < treshold_seconds
#
# def load_dataframes(coins, hourly_cols, start_date):
#     df_prices = load_data('data', coins, start_date)
#     df_hourly = load_data('data_hourly', hourly_cols, start_date)
#     df_hourly = df_hourly.resample('1H', closed='right').pad() # resample to nearest cieling hour
#     is_ok_time_diff = len(df_prices[list(df_prices.reset_index()['timestamp'].diff().dt.total_seconds() > 120)]) == 0
#     assert is_ok_time_diff , 'There are instances with larger time diff'
#     print(df_prices.index[-1])
#     if not is_time_updated(df_prices.index[-1]):
#         print('ALERT- database not updated, wait or check process')
#     return df_prices, df_hourly
#
# df_prices, df_hourly = load_dataframes(coins, hourly_cols, start_date)
# print(df_prices.shape, df_hourly.shape)
