import pandas as pd

from AStock.sectors import get_daily_data, all_etf_longname


def check_ticker(data, day_shift=1):
    print('Relative to date: ', data.index[-day_shift].date())
    tickers = set([x[0] for x in data.columns.tolist()])

    # print(len(data))

    def change_pct(new, old):
        return new / old - 1

    def add_sma_pct(series, len):
        df_t[f'sma{len}_pct'] = change_pct(series.rolling(len).mean(), series)

    res = pd.DataFrame()
    for ticker in tickers:
        df_t = data[ticker][['Close', 'Volume']]
        close = df_t['Close']
        add_sma_pct(close, 20)
        add_sma_pct(close, 50)
        add_sma_pct(close, 150)
        # add_sma_pct(df_t, 200)
        # dist to sma, if below, will be positive, if above, should be negative
        curr_row = df_t.iloc[-day_shift]
        curr_row.name = ticker
        res = pd.concat([res, curr_row.to_frame()], axis=1)
    # [['Close', 'Volume']]
    res = res.T
    return res


def print_pct_html(df):
    pct_cols = [c for c in df.columns if c.endswith('_pct')]
    out_df = df
    out_df = out_df.style.background_gradient(subset=pct_cols, cmap='RdYlGn', vmin=-0.3, vmax=.3, axis=0)
    out_df = out_df.format({c: '{:.2%}' for c in pct_cols})
    out_df.to_html('check.html',
                   classes=["table-bordered", "table-striped",
                            "table-hover"])


def get_swings():
    crypto = ['MARA', 'HUT', 'MSTR', 'RIOT', 'COIN']
    # FILTER GROWTH VS VALUE STOCK
    fintech = ['AFRM', 'SOFI', 'PYPL', 'SQ', 'UPST', 'LMND']
    big_tech = ['TSLA', 'AAPL', 'MSFT', 'GOOGL', 'META', ]
    semi = ['NVDA', 'AMD', 'MU', 'TXN', 'TSM']
    cyber = ['CRWD', 'S']
    saas = ['MNDY', 'DDOG', 'DASH', 'PATH', 'SNOW', 'CRM']
    chinese = ['BABA', 'NIO']
    other = ['RBLX', 'ROKU', 'DIS', 'NFLX', 'BA', ]
    green = ['SEDG', 'ENPH']
    consumer = ['AMZN', 'SHOP', 'CHWY', 'RIVN', 'LULU']
    medical = ['TDOC', 'MRNA']
    indexes = ['SPY', 'QQQ', 'IWM', 'DIA', 'SOXX']  # 'RTY=F'
    customer_service = ['WING', 'CROX', 'LOVE', 'UBER']
    # all_etf_longname
    tickers = crypto + fintech + big_tech + semi + cyber + saas + chinese + other + green + consumer + medical + customer_service + indexes
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

    # print_pct_html(res)


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
