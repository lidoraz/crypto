import pandas as pd


def resample_ohlcv_higher_1d(ohlcv, interval):
    ohlcv = pd.concat([
        ohlcv['open'].resample(interval).first(),
        ohlcv['high'].resample(interval).max(),
        ohlcv['low'].resample(interval).min(),
        ohlcv['close'].resample(interval).last(),
        ohlcv['volume'].resample(interval).sum()], axis=1)
    return ohlcv


def get_data_nasdaq(full_path, interval, filter_ts=False):
    df_ohlcv = pd.read_csv(full_path, index_col='Date')
    df_ohlcv.index = pd.to_datetime(df_ohlcv.index)
    df_ohlcv.columns = [c.lower() for c in df_ohlcv.columns]
    if pd.to_timedelta(interval, unit='D').days > 1:
        df_ohlcv = _resample_ohlcv_higher_1d(df_ohlcv, interval)
    if filter_ts:
        start_ts = df_ohlcv.index[-1] - pd.to_timedelta(interval, unit='D') * 200
        df_ohlcv = df_ohlcv[df_ohlcv.index > start_ts]
        # print(start_ts)
    df_ohlcv.attrs['interval'] = interval
    return df_ohlcv
