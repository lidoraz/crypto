import pandas as pd
from datetime import datetime
from AStock.sectors import get_daily_data, all_etf_longname
from AStock.util import plot_ohlc_daily
from Indicators import RSI, TheStratInd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


def check_ticker(data, day_shift=1, minimum_volume=1e6 / 2):
    print('Relative to date: ', data.index[-day_shift].date())
    tickers = set([x[0] for x in data.columns.tolist()])

    # print(len(data))

    def change_pct(new, old):
        return new / old - 1

    def add_sma_pct(ohlc, len):
        close = ohlc['close']
        return change_pct(close.rolling(len).mean(), close).rename(f'sma{len}_pct')

    res = pd.DataFrame()

    # x = list(df_t['Volume'].rolling(5))[-1]
    def calc_volume_change(df):
        n = 5
        # vol_pct = df['Volume'].rolling(n).pct_change()
        # price_pct = df['Close'].rolling(n).pct_change()
        # Calculating only last 5 rows, needs to join them to the main table, this currently does not work.
        last_row_vol = [x.pct_change().values for x in list(df['volume'][-n:].rolling(n))][-1][1:]
        last_row_price = df['change_pct'][-n + 1:].values
        return pd.Series(zip(last_row_vol, last_row_price)).rename('vol_price_trend')

    def volume_thumbnail(df_t, lk):
        lat_df = df_t[-lk:]
        color_bars = ['green' if x['close'] > x['open'] else 'red' for _, x in lat_df.iterrows()]
        plt.bar(range(lk), lat_df['volume'], color=color_bars)
        plt.axis('off')
        plt.savefig(f'img/{ticker}.png', bbox_inches='tight')
        plt.clf()

    def candle_stick_thumbnail(df, lk):
        df_t = df[-lk:]
        fig = plot_ohlc_daily(df_t)
        plt.axis('off')
        plt.savefig(f'img/{ticker}_ohlc.png')
        plt.clf()

    for ticker in tickers:
        df_t = data[ticker]
        df_t.columns = [c.lower() for c in df_t.columns]
        # minimum volume req:
        if df_t['volume'].rolling(14).mean()[-1] < minimum_volume:
            print(f'Filtered out ticker: {ticker} due to low avg volume')
            continue
        # df_tdf_t.rename(columns={'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low'}))
        df_t = df_t.join((df_t['close'] / df_t['close'].shift(1) - 1).rename('d_chg_pct'))
        df_t = df_t.join((df_t['close'] / df_t['close'].shift(7) - 1).rename('w_chg_pct'))
        # df_t = df_t.join(calc_volume_change(df_t)) # TEST THIS
        df_t = df_t.join(add_sma_pct(df_t, 20))
        df_t = df_t.join(add_sma_pct(df_t, 50))
        df_t = df_t.join(add_sma_pct(df_t, 150))
        # df_t = df_t.join(add_sma_pct(df_t, 200))
        df_t = df_t.join(add_cci(df_t, 14))
        df_t = df_t.join(RSI(14).calc(df_t))
        df_t = df_t.join(TheStratInd(False).calc(df_t[-5:]).fillna(''))
        # add_sma_pct(df_t, 200)
        # dist to sma, if below, will be positive, if above, should be negative

        # curr_row = curr_row # [['Close', 'Volume']]
        # curr_row.name = ticker
        volume_thumbnail(df_t, 5)
        # candle_stick_thumbnail(df_t, 10)
        curr_row = df_t.iloc[-day_shift].rename(ticker)
        curr_row = curr_row.drop(['adj close', 'open', 'high', 'low'])  # 'High', 'Low'
        curr_row['profile_volume'] = f'<img src="img/{ticker}.png" height="27px"/>'
        res = pd.concat([res, curr_row.to_frame()], axis=1)
    # [['Close', 'Volume']]
    res = res.T
    return res


def add_cci(ohlc, length):
    src = ohlc[['high', 'low', 'close']].sum(axis=1) / 3
    ma = ohlc['close'].rolling(length).mean()
    dev = ohlc['close'].rolling(length).std()
    cci = (src - ma) / (0.015 * dev)
    return pd.Series(cci).rename(f'cci_{length}').round(2)


def print_apply_html_formats(df):
    pct_cols = [c for c in df.columns if c.endswith('pct')]
    cci_cols = [c for c in df.columns if c.startswith('cci_')]
    # df = df.round(2)
    # df['Volume'] = df['Volume'].apply(lambda x: f'{x / 1e6:0.1f}M')
    out_df = df.style
    out_df = out_df.background_gradient(subset=pct_cols, cmap='RdYlGn', vmin=-0.25, vmax=.25, axis=0)
    out_df = out_df.background_gradient(subset=['d_chg_pct', 'w_chg_pct'], cmap='RdYlGn', vmin=-0.07, vmax=.07, axis=0)
    out_df = out_df.background_gradient(subset=cci_cols, cmap='RdYlGn_r', vmin=-101, vmax=101, axis=0)
    out_df = out_df.background_gradient(subset='RSI14', cmap='RdYlGn_r', vmin=30, vmax=70, axis=0)

    def color_combo(combo):
        color = 'White'
        if 'RL' in combo:
            color = '#006837'
        elif 'CL' in combo:
            color = '#1a9850'
        elif 'RS' in combo:
            color = '#a50026'
        elif 'CS' in combo:
            color = '#d73027'
        return f'background-color: {color}; color: white'

    out_df = out_df.applymap(subset=['thestrat_combo'], func=color_combo)

    out_df = out_df.set_properties(**{'text-align': 'center'})
    strat_cols = ['thestrat_num', 'cnd_color', 'thestrat_combo', 'thestrat_cnd_type', 'profile_volume']

    # out_df.applymap(subset=['cnd_color' , 'thestrat_combo'], func=lambda v: "color:pink;" if v>4 else "color:darkblue;")
    formatters = {c: '{:.2f}' for c in df.columns if c not in strat_cols}

    formatters['volume'] = lambda x: "{:.1f}M".format(x * 1e-6)
    formatters.update({c: '{:.2%}' for c in pct_cols})
    formatters['close'] = '${:.2f}'
    out_df = out_df.format(formatters)
    return out_df


def print_pct_html(df_index, df_stocks, data_date):
    out_df1 = print_apply_html_formats(df_index)
    out_df2 = print_apply_html_formats(df_stocks)
    out_df1 = out_df1.set_caption(f'<h1>Selected tickers, Relevant to date: {data_date}</h1>')
    out_df1_html = out_df1.to_html()
    out_df2_html = out_df2.to_html()
    # out_df.to_html('check.html',
    #                classes=["table-bordered", "table-striped",
    #                         "table-hover"])
    # highlighted = out_df.set_caption(f'<h1>Selected tickers, Relevant to date: {data_date}</h1>')
    # # render() generates the HTML for the Styler object
    with open('check.html', 'w') as f:
        out = out_df1_html + '\n' + out_df2_html
        f.write(out)


def filter_nulls(data):
    null_tickers = data.isnull().sum(axis=0) != 0
    null_tickers = null_tickers[null_tickers].index.tolist()
    null_tickers = set([t[0] for t in null_tickers])
    if len(null_tickers):
        print('Couldnt fetch these tickers:', null_tickers)
        data = data.drop(columns=null_tickers)
    return data


def get_swings():
    high_growth = ['AFRM', 'AMD', 'CFLT', 'CRWD', 'DDOG', 'DLO', 'GLBE', 'GTLB', 'MELI', 'NET', 'NVDA',
                   'OKTA', 'OPEN', 'RBLX', 'S', 'SHOP', 'SNOW', 'SOFI', 'TOST', 'TSLA', 'TWLO', 'ZI', 'ARKK', 'WOLF',
                   'MNDY', 'BILL', 'ENPH', 'ASAN', 'ESTC', 'TEAM', 'IOT', 'HCP', 'ZS', 'U', 'MDB', 'SEDG', 'DAVA',
                   'ENTG', 'FSLR', 'GLOB', 'PLTR', 'TTD', 'HUBS', 'NOW', 'PATH', 'PCOR', 'EPAM', 'PAYC', 'FIVN', 'CYBR',
                   'DT', 'FTNT', 'PCTY', 'ZEN', 'APP', 'PANW', 'AVLR', 'PAGS']
    crypto = ['MARA', 'HUT', 'MSTR', 'RIOT', 'COIN']
    # FILTER GROWTH VS VALUE STOCK
    fintech = ['AFRM', 'SOFI', 'PYPL', 'SQ', 'UPST', 'LMND']
    big_tech = ['TSLA', 'AAPL', 'MSFT', 'GOOGL']
    semi = ['NVDA', 'AMD', 'MU', 'TXN', 'TSM']  # 'ASML', 'AMAT'
    cyber = ['CRWD', 'S', 'PANW', 'CYBR']
    saas = ['MNDY', 'DDOG', 'DASH', 'PATH', 'SNOW', 'CRM', 'VEEV']
    internet_software = ['META', 'GOOGL', 'PINS', 'ADBE']
    chinese = ['BABA', 'NIO', 'JD', ]
    other = ['RBLX', 'ROKU', 'DIS', 'NFLX', 'BA', ]
    green = ['SEDG', 'ENPH']
    consumer = ['AMZN', 'SHOP', 'CHWY', 'RIVN', 'LULU']
    internet_retail = ['AMZN', 'CHWY', 'LULU']

    medical = ['TDOC', 'MRNA']
    indexes = ['SPY', 'QQQ', 'IWM', 'DIA', 'SOXX', 'ARKK']  # 'RTY=F'
    customer_service = ['WING', 'CROX', 'LOVE', 'UBER']
    # all_etf_longname
    tickers = crypto + fintech + big_tech + semi + cyber + internet_software + saas + chinese + internet_retail + other + green + consumer + medical + customer_service + indexes
    tickers = high_growth + indexes + tickers
    tickers = list(set(tickers))
    data = get_daily_data(tickers, days_before=300, group_by='ticker')
    # data = data[:-days_before]
    time_now = datetime.utcnow()
    if data.iloc[-1].isna().all():
        # if time_now.hour < 11 or time_now.hour == 13 and time_now.minute < 31:
        data = data[:-1]
        print(f'Calculating for date: {data.index[-1].date()}')
    data_date = str(data.index[-1].date())
    # data = filter_nulls(data)

    df = check_ticker(data)

    print('-> Indexes')

    df_index = df[df.index.isin(indexes)]
    # print_pct(res_indexes.sort_values('sma20_pct', ascending=False))
    pprint_screener(df_index)
    print('-> Stocks')
    df_stocks = df[~df.index.isin(indexes)]
    # LONG - should be far from sma20, SHORT- higher than sma 20.
    # df_stocks = df_stocks.sort_values('sma20_pct', ascending=False)  # check long potentials
    df_stocks = df_stocks.sort_values(['sma20_pct', 'cnd_color', ], ascending=[False, True, ])  # check long potentials
    # CHECK RSI, and CCI, check also for volume decrease for sells.
    # check that close price is not far from open, look for doji, or bullish, also can use thestrat for indicator.
    pprint_screener(df_stocks)

    print_pct_html(df_index, df_stocks, data_date)


def pprint_screener(df):
    df = df.copy()
    df['volume'] = df['volume'].apply(lambda x: f'{x / 1e6:0.1f}M')
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
    days_before = 0  # 11
    get_swings()
