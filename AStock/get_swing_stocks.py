import pandas as pd

from AStock.sectors import get_daily_data, all_etf_longname
from Indicators import RSI


def check_ticker(data, day_shift=1):
    print('Relative to date: ', data.index[-day_shift].date())
    tickers = set([x[0] for x in data.columns.tolist()])

    # print(len(data))

    def change_pct(new, old):
        return new / old - 1

    def add_sma_pct(ohlc, len):
        close = ohlc['Close']
        return change_pct(close.rolling(len).mean(), close).rename(f'sma{len}_pct')

    res = pd.DataFrame()

    for ticker in tickers:
        df_t = data[ticker]
        df_t = df_t.join((df_t['Close'] / df_t['Close'].shift(1) - 1).rename('change_pct'))
        df_t = df_t.join(add_sma_pct(df_t, 20))
        df_t = df_t.join(add_sma_pct(df_t, 50))
        df_t = df_t.join(add_sma_pct(df_t, 150))
        df_t = df_t.join(add_sma_pct(df_t, 200))
        df_t = df_t.join(add_cci(df_t, 14))
        df_t = df_t.join(RSI(14).calc(df_t.rename(columns={'Close': 'close'})))
        # add_sma_pct(df_t, 200)
        # dist to sma, if below, will be positive, if above, should be negative
        curr_row = df_t.iloc[-day_shift].rename(ticker)
        curr_row = curr_row.drop(['Adj Close', 'Open', 'High', 'Low'])  # 'High', 'Low'
        # curr_row = curr_row # [['Close', 'Volume']]
        # curr_row.name = ticker
        res = pd.concat([res, curr_row.to_frame()], axis=1)
    # [['Close', 'Volume']]
    res = res.T
    return res


def add_cci(ohlc, length):
    src = ohlc[['High', 'Low', 'Close']].sum(axis=1) / 3
    ma = ohlc['Close'].rolling(length).mean()
    dev = ohlc['Close'].rolling(length).std()
    cci = (src - ma) / (0.015 * dev)
    return pd.Series(cci).rename(f'cci_{length}').round(2)


def print_pct_html(df):
    pct_cols = [c for c in df.columns if c.endswith('pct')]
    cci_cols = [c for c in df.columns if c.startswith('cci_')]
    # df = df.round(2)
    # df['Volume'] = df['Volume'].apply(lambda x: f'{x / 1e6:0.1f}M')

    out_df = df.style
    out_df = out_df.background_gradient(subset=pct_cols, cmap='RdYlGn', vmin=-0.25, vmax=.25, axis=0)
    out_df = out_df.background_gradient(subset='change_pct', cmap='RdYlGn', vmin=-0.07, vmax=.07, axis=0)
    out_df = out_df.background_gradient(subset=cci_cols, cmap='RdYlGn', vmin=-101, vmax=101, axis=0)
    out_df = out_df.background_gradient(subset='RSI14', cmap='RdYlGn', vmin=30, vmax=70, axis=0)
    formatters = {c: '{:.2f}' for c in df.columns}
    formatters['Volume'] = lambda x: "{:.1f}M".format(x * 1e-6)
    formatters.update({c: '{:.2%}' for c in pct_cols})
    formatters['Close'] = '${:.2f}'
    # lambda x: "$ {:,.1f}".format(x*-1e6)
    out_df = out_df.format(formatters)
    # out_df = out_df.format({c: '{:.2%}' for c in pct_cols})
    out_df.to_html('check.html',
                   classes=["table-bordered", "table-striped",
                            "table-hover"])


def get_swings():
    high_growth = ['AFRM', 'AMD', 'BTCUSD', 'CFLT', 'CRWD', 'DDOG', 'DLO', 'GLBE', 'GTLB', 'MELI', 'NET', 'NVDA',
                   'OKTA', 'OPEN', 'RBLX', 'S', 'SHOP', 'SNOW', 'SOFI', 'TOST', 'TSLA', 'TWLO', 'ZI', 'ARKK', 'WOLF',
                   'MNDY', 'BILL', 'ENPH', 'ASAN', 'ESTC', 'TEAM', 'IOT', 'HCP', 'ZS', 'U', 'MDB', 'SEDG', 'DAVA',
                   'ENTG', 'FSLR', 'GLOB', 'PLTR', 'TTD', 'HUBS', 'NOW', 'PATH', 'PCOR', 'EPAM', 'PAYC', 'FIVN', 'CYBR',
                   'MNDT', 'DT', 'FTNT', 'PCTY', 'ZEN', 'APP', 'PANW', 'AVLR', 'PAGS']
    crypto = ['MARA', 'HUT', 'MSTR', 'RIOT', 'COIN']
    # FILTER GROWTH VS VALUE STOCK
    fintech = ['AFRM', 'SOFI', 'PYPL', 'SQ', 'UPST', 'LMND']
    big_tech = ['TSLA', 'AAPL', 'MSFT', 'GOOGL']
    semi = ['NVDA', 'AMD', 'MU', 'TXN', 'TSM']  # 'ASML', 'AMAT'
    cyber = ['CRWD', 'S', 'PANW', 'CYBR']
    saas = ['MNDY', 'DDOG', 'DASH', 'PATH', 'SNOW', 'CRM', 'VEEV']
    internet_software = ['META', 'GOOGL', 'PINS', 'TWTR']
    chinese = ['BABA', 'NIO', 'JD', ]
    other = ['RBLX', 'ROKU', 'DIS', 'NFLX', 'BA', ]
    green = ['SEDG', 'ENPH']
    consumer = ['AMZN', 'SHOP', 'CHWY', 'RIVN', 'LULU']
    internet_retail = ['AMZN', 'CHWY', 'LULU']

    medical = ['TDOC', 'MRNA']
    indexes = ['SPY', 'QQQ', 'IWM', 'DIA', 'SOXX']  # 'RTY=F'
    customer_service = ['WING', 'CROX', 'LOVE', 'UBER']
    # all_etf_longname
    tickers = crypto + fintech + big_tech + semi + cyber + internet_software + saas + chinese + internet_retail + other + green + consumer + medical + customer_service + indexes
    tickers = high_growth + indexes
    tickers = list(set(tickers))
    data = get_daily_data(tickers, days_before=300, group_by='ticker')

    null_tickers = data.isnull().sum(axis=0) != 0
    null_tickers = null_tickers[null_tickers].index.tolist()
    if len(null_tickers):
        print('Couldnt fetch these tickers:', null_tickers)
    import pandas as pd

    res = check_ticker(data)

    print('-> Indexes')

    res_indexes = res[res.index.isin(indexes)]
    # print_pct(res_indexes.sort_values('sma20_pct', ascending=False))
    pprint_screener(res_indexes)
    print('-> Stocks')
    res = res[~res.index.isin(indexes)]
    # LONG - should be far from sma20, SHORT- higher than sma 20.
    res = res.sort_values('sma20_pct', ascending=False)  # check long potentials
    # CHECK RSI, and CCI, check also for volume decrease for sells.
    # check that close price is not far from open, look for doji, or bullish, also can use thestrat for indicator.
    pprint_screener(res)

    print_pct_html(res)


def pprint_screener(df):
    df = df.copy()
    df['Volume'] = df['Volume'].apply(lambda x: f'{x / 1e6:0.1f}M')
    pct_cols = [c for c in df.columns if c.endswith('_pct')]
    df = df.sort_values('sma20_pct', ascending=False)
    df[pct_cols] = df[pct_cols].applymap(lambda x: f'{x:.2%}')
    # out_df = out_df.style.format({c: '{:.2%}' for c in pct_cols})
    # df = df.format()
    print(df)


def get_short_interset():
    url = "https://www.benzinga.com/short-interest/most-shorted"
    import requests
    # import beatifulsoup # not installed
    res = requests.get(url)
    # import
    table_class = "ant-table-body"
    last_updated_class = "last-updated"


if __name__ == '__main__':
    get_swings()
