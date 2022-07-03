import yfinance as yf
import time
import pandas as pd

from Nasdaq.recommend import add_info_symbols

market_etf = ['SPY', 'QQQ']
gap_size_pct_min = 0.01
gap_size_pct_large = 0.04

def extract_market_type(dt):
    # TRADING IN STOCKS: MONDAY TO FIRDAY, there are special days too,
    # PREMARKET - 4am to 9:30am
    # MARKET - 9:30am to 16pm
    # POST - 4pm to 8pm
    if dt.hour == 9 and dt.minute >= 30 or 10 <= dt.hour <= 15 or dt.hour == 16 and dt.minute == 0:
        return 'MARKET'
    if 4 <= dt.hour < 9 or dt.hour == 9 and dt.minute < 30:
        return 'PRE'
    if dt.hour == 16 and dt.minute > 0 or 17 <= dt.hour < 20:
        return 'POST'
    return 'INVALID'


def get_stock_data(symbols):
    t0 = time.time()
    end = int(time.time())
    days_before = 6
    start = end - 60 * 60 * 24 * days_before  # 1 day before
    start = pd.to_datetime(start, unit='s', utc=True)

    data = yf.download(' '.join(symbols), start=start, end=None,
                       prepost=True,  # include pre/post market data
                       rounding=True,
                       actions=True,  # dividend + stock splits data
                       group_by='ticker',  # default is on columns. ticker is easier to iterate
                       auto_adjust=False,  # false on default, what does it do?
                       show_errors=True,
                       interval='1m', threads=True, progress=False)
    print(f"start={start}, data: {str(data.index[-1])} took: {time.time() - t0:0.2f}")
    data['DT'] = data.index
    data['Date'] = data.index.date
    data['Type'] = data['DT'].apply(extract_market_type)
    return data


def add_addional_cols_to_symbol(symbol, data):
    cols = ['Type', 'Date']
    df_symbol = data[symbol].copy()
    df_symbol[cols] = data[cols]
    return df_symbol


# Take last row not null from POST
# Take last row not null from PRE,
# Compare them.
def get_post_to_pre_gap(df_symbol, curr_date):
    ## compare post to pre POST -> PRE in order to find large gaps. higher than 3% is intersting.
    curr_date = curr_date.date()
    df_symbol = df_symbol[df_symbol['Date'] <= curr_date]
    #     print(df_symbol.index[-1])
    df_g = df_symbol.groupby(['Date', 'Type'])['Adj Close'].agg(['last']).reset_index()
    closing_row = df_g[df_g['Type'] == 'MARKET'].sort_values('Date').iloc[-1]
    today_row = df_g[df_g['Type'] == 'PRE'].sort_values('Date').iloc[-1]
    closing_price = closing_row['last']
    today_pre_price = today_row['last']
    assert today_row['Date'] == curr_date, 'sanity for currdate'
    #     display(df_g[-6:])  # DEBUG
    meta = dict(today_pre_price=today_pre_price, closing_price=closing_price)
    return today_pre_price / closing_price - 1, meta


def closed_the_gap(df_symbol, gap_pct, curr_date):
    #     curr_date = pd.to_datetime('2022-06-17').date()
    df_t = df_symbol[(df_symbol['Date'] == curr_date.date()) & (df_symbol['Type'] == 'MARKET')]
    #     display(df_t[:10])
    start_gap = df_t.iloc[0]['Open'] * (1 - gap_pct)
    s_t_high = df_t['High']
    s_t_low = df_t['Low']
    #     print('start_gap',start_gap)
    meta = None
    treshold = 0.01  # allow slight deviation closing the gap can be almost
    if gap_pct > 0:
        t = s_t_low[s_t_low < start_gap * (1 + treshold)].head(1)
    else:
        t = s_t_high[s_t_high > start_gap * (1 - treshold)].head(1)
    is_passed = len(t) > 0
    if is_passed:
        meta = dict(at=t.index[0], v=t.values[0], start_gap=start_gap)

    return is_passed, meta


# closed_the_gap(df_symbol, 0.01)
# color = "🟢" if chg_pct > 0 else "🔴"
# gap_type = "(** Large **)" if is_large else "(Small)"
#             print(f'{symbol}, {chg_pct:0.2%}{color} {gap_type}')

# curr_price =

def conv_df(df):
    dff = df.copy()
    apply_dict = dict(chg_pct=lambda x: f'{x:0.2%}',
                      volume_M=lambda x: f'{x:0.1f}',
                      is_large_gap=lambda x: 'LARGE' if x else 'small')
    for k, v in apply_dict.items():
        dff[k] = dff[k].apply(v)
    return dff


def df_to_dict_lst(df):
    return [row.to_dict() for _, row in df.iterrows()]


def find_gaps(symbols, add_info=False):
    dt_now = pd.to_datetime(int(time.time()), unit='s', utc=True)
    dt_now_broker = dt_now.tz_convert('America/New_York')
    # dt_now_broker = pd.to_datetime('2022-06-28')
    print('dt_now_broker', dt_now_broker)
    data = get_stock_data(symbols)
    df_gaps = go_over_symbols_premarket(symbols, data, dt_now_broker)
    df_etf = df_gaps[df_gaps['symbol'].isin(market_etf)]
    # Split to negative and positive
    df_gaps = df_gaps[~df_gaps['symbol'].isin(market_etf)]
    # Add symbol data
    symbols_no_etf = symbols - set(market_etf)
    if add_info:
        # TODO: Maybe add news for snp
        symbols_additional_info = add_info_symbols(symbols_no_etf, dt_now_broker)
        df_gaps = df_gaps.merge(symbols_additional_info, on='symbol')

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    print('----> Market Directions:')
    print(conv_df(df_etf))
    vol_filter = 2
    print(f'\nFiltering only over {vol_filter}M volume')
    df_gaps = df_gaps[df_gaps['volume_M'] > vol_filter]
    # positive:
    print('----> Positive Change')
    df_pos = df_gaps[df_gaps['chg_pct'] > 0.01].sort_values('chg_pct', ascending=False)
    print(conv_df(df_pos))
    print('\n----> Negatigve Change')
    df_neg = df_gaps[df_gaps['chg_pct'] < -0.01].sort_values('chg_pct', ascending=True)
    print(conv_df(df_neg))
    print('Done!')

    output = dict(etf=df_to_dict_lst(conv_df(df_neg)),
                  pos=df_to_dict_lst(conv_df(df_pos)),
                  neg=df_to_dict_lst(conv_df(df_neg)))
    import json

    with open('output.json', 'w') as f:
        json.dump(output, f)



def go_over_symbols_premarket(symbols, data, dt_now):
    gap_data = []
    curr_data_dt = data.index.max()
    print(f"Relevant to: {curr_data_dt}, type: {extract_market_type(curr_data_dt)}")
    for symbol in symbols:
        df_symbol = add_addional_cols_to_symbol(symbol, data)
        chg_pct, _ = get_post_to_pre_gap(df_symbol, dt_now)
        is_large = abs(chg_pct) > gap_size_pct_large
        has_gap = abs(chg_pct) > gap_size_pct_min
        volume_last_trading_day = df_symbol['Volume'].groupby(df_symbol.index.date).sum()[-2] / 1e6
        gap_data.append(dict(symbol=symbol, chg_pct=chg_pct, has_gap=has_gap, is_large_gap=is_large, volume_M=volume_last_trading_day))
    gap_data = pd.DataFrame(gap_data).sort_values(['chg_pct'], ascending=[False])
    return gap_data


def check_one_gap():  # Test
    data = get_stock_data(['AAPL'])
    df_symbol = add_addional_cols_to_symbol('SPY', data)
    dt_now = pd.to_datetime(int(time.time()), unit='s')
    # dt_now = pd.to_datetime('2022-06-24T09:10+ -04', utc=True)
    get_post_to_pre_gap(df_symbol, dt_now)


def snp500_stocks(limit=None):
    df = pd.read_csv('snp500.csv')
    symbols = df['Symbol'][:limit].tolist()
    symbols = symbols + ['SPY', 'QQQ']
    return symbols


def selected_stocks():
    main = ['AAPL', 'TSLA', 'MSFT', 'AMZN', 'META', 'BABA', 'NFLX', 'NVDA', 'BA', 'ADBE', 'V']
    etf = ['SPY', 'QQQ']
    ev = ['LCID', 'NIO', 'RIVN', 'F', 'GM']
    chinese = ['BABA', 'BIDU', 'JD']
    flag = ['DDOG', 'XOM']  # one huge PE, 2nd very weak, had very bad week
    crypto = ['COIN']
    symbols = etf + main + ev + flag + crypto + chinese
    return symbols


if __name__ == '__main__':
    # MAYBE ADD VOLATILITY DURING PREMARKT - something like the GAP rules for snp500
    symbols = snp500_stocks(150)
    # TODO: ADD NASDAQ 100
    # symbols = []
    symbols = set(symbols + selected_stocks())
    # FILTER STOCKS WITH VOLUME HIGHER THAN 1M STOCKS PER DAY.
    pd.set_option('display.max_rows', 500)
    find_gaps(symbols, add_info=True)
    # TODO: Add If there is a calndar special thing, like earnings
    # TODO: Add IPO, splits, Earnings, dividends, options etc... prior to market
    # TODO: P/E, anaylsis, something that could attracts other investors.
