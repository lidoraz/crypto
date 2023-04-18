import pandas as pd
from datetime import datetime

from AStock.insider_buy import put_object_stocks
from AStock.util import plot_ohlc_daily, get_daily_data
from Indicators import RSI, TheStratInd
import requests
import matplotlib
import base64

matplotlib.use('Agg')
import matplotlib.pyplot as plt

file_name = 'daily_swing.html'

high_growth = ['AFRM', 'AMD', 'CFLT', 'CRWD', 'DDOG', 'DLO', 'GLBE', 'GTLB', 'MELI', 'NET', 'NVDA',
               'OKTA', 'OPEN', 'RBLX', 'S', 'SHOP', 'SNOW', 'SOFI', 'TOST', 'TSLA', 'TWLO', 'ZI', 'ARKK', 'WOLF',
               'MNDY', 'BILL', 'ENPH', 'ASAN', 'ESTC', 'TEAM', 'IOT', 'HCP', 'ZS', 'U', 'MDB', 'SEDG', 'DAVA',
               'ENTG', 'FSLR', 'GLOB', 'PLTR', 'TTD', 'HUBS', 'NOW', 'PATH', 'PCOR', 'EPAM', 'PAYC', 'FIVN', 'CYBR',
               'DT', 'FTNT', 'PCTY', 'APP', 'PANW', 'PAGS']
crypto = ['MARA', 'HUT', 'MSTR', 'RIOT', 'COIN']
# FILTER GROWTH VS VALUE STOCK
fintech = ['AFRM', 'SOFI', 'PYPL', 'SQ', 'UPST', 'LMND']
big_tech = ['TSLA', 'AAPL', 'MSFT', 'GOOGL']
semi = ['NVDA', 'AMD', 'MU', 'TXN', 'TSM']  # 'ASML', 'AMAT'
cyber = ['CRWD', 'S', 'PANW', 'CYBR']
saas = ['MNDY', 'DDOG', 'DASH', 'PATH', 'SNOW', 'CRM', 'VEEV']
internet_software = ['META', 'GOOGL', 'PINS', 'ADBE']
chinese = ['BABA', 'NIO', 'JD', ]
other = ['RBLX', 'ROKU', 'DIS', 'NFLX', 'BA', "ZIM", "GS", "SCHW"]
green = ['SEDG', 'ENPH']
consumer = ['AMZN', 'SHOP', 'CHWY', 'RIVN', 'LULU']
internet_retail = ['AMZN', 'CHWY', 'LULU']

medical = ['TDOC', 'MRNA', "JNJ"]
indexes = ['SPY', 'QQQ', 'IWM', 'DIA', 'SOXX', 'ARKK']  # 'RTY=F'
sector_indexes = ["XLK", "XLC", "XLU", "XLRE", "XLB", "XLP", "XLI", "XLY", "XLV", "XLE", "XLF"]
customer_service = ['WING', 'CROX', 'LOVE', 'UBER']


# ADD VIX TICKERS FOR BAROMETER: ^VIX, ^VIX9D, ^VIX3M
# all_etf_longname


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
        plt.savefig(f'AStock/img/{ticker}.png', bbox_inches='tight')
        plt.clf()

    def candle_stick_thumbnail(df, lk):
        df_t = df[-lk:]
        fig = plot_ohlc_daily(df_t)
        plt.axis('off')
        plt.savefig(f'AStock/img/{ticker}_ohlc.png')
        plt.clf()

    for ticker in tickers:
        df_t = data[ticker]
        df_t.columns = [c.lower() for c in df_t.columns]
        # minimum volume req:
        if df_t['volume'].rolling(14).mean()[-1] < minimum_volume:
            print(f'Filtered out ticker: {ticker} due to low avg volume')
            continue

        # df_tdf_t.rename(columns={'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low'}))
        def sub_dates_closest(df, days_back):
            for delta in range(7):
                index = df.index[-1] - pd.to_timedelta(f"{days_back + delta}D")
                if index in df.index:
                    return df.loc[index]

        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 1)['close'] - 1).rename('D_chg_pct'))
        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 7)['close'] - 1).rename('W_chg_pct'))
        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 14)['close'] - 1).rename('2W_chg_pct'))
        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 30)['close'] - 1).rename('M_chg_pct'))
        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 90)['close'] - 1).rename('Q_chg_pct'))
        df_t = df_t.join((df_t['close'] / sub_dates_closest(df_t, 365)['close'] - 1).rename('Y_chg_pct'))
        # df_t = df_t.join(calc_volume_change(df_t)) # TEST THIS
        df_t = df_t.join(add_sma_pct(df_t, 20))
        df_t = df_t.join(add_sma_pct(df_t, 50))
        df_t = df_t.join(add_sma_pct(df_t, 150))
        df_t = df_t.join(add_sma_pct(df_t, 200))
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
        with open(f'AStock/img/{ticker}.png', 'rb') as f:
            b64 = base64.b64encode(open(f'AStock/img/{ticker}.png', 'rb').read()).decode("utf-8")
            src_b64 = f"data: image/png; base64,{b64}"
            curr_row['profile_volume'] = f'<img src="{src_b64}" height="27px"/>'
        # curr_row['profile_volume'] = f'<img src="img/{ticker}.png" height="27px"/>'
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
    cci_cols = [c for c in df.columns if c.startswith('cci_')]
    df.columns = [c.replace("thestrat_", "") for c in df.columns]
    df.columns = [c.replace("_chg_pct", "") for c in df.columns]
    pct_cols = {"D": 0.08, "W": 0.15, "2W": 0.15, "M": 0.2, "Q": 0.25, "Y": 0.5, "sma20_pct": 0.1, "sma50_pct": 0.15,
                "sma150_pct": 0.2, "sma200_pct": 0.3}
    mapper = {"Hammer": "🔨", "Shooter": "🔫"}
    df['cnd_type'] = df['cnd_type'].apply(lambda x: mapper.get(x, ""))
    img_ticker_s = '<div class="cont-img"> <img src="https://financialmodelingprep.com/image-stock/{}.png" class="ticker-img" /></div>'
    df['Ticker'] = df.index.values
    df[' '] = df['Ticker'].apply(lambda x: img_ticker_s.format(x))
    # df.index.name = "Ticker"
    df = df.rename(columns={"cnd_color": "c", "cnd_type": "t", "profile_volume": "Vol", "index": "Ticker"})
    cols = ['Ticker', ' ', 'close', 'D', 'W', '2W', 'M', 'Q', 'Y', 'Vol', 'sma20_pct', 'sma50_pct', 'sma150_pct', 'sma200_pct',
            'cci_14', 'RSI14', 'num', 'c', 't', 'combo', 'volume']
    df = df[cols]
    out_df = df.style
    for pct_col, vmax in pct_cols.items():
        out_df = out_df.background_gradient(subset=pct_col, cmap='RdYlGn', axis=0, vmin=-vmax,
                                            vmax=vmax)
    out_df = out_df.background_gradient(subset=cci_cols, cmap='RdYlGn_r', vmin=-101, vmax=101, axis=0)
    out_df = out_df.background_gradient(subset='RSI14', cmap='RdYlGn_r', vmin=30, vmax=70, axis=0)
    # format_cols = ["price", "cci_14", "RSI14"]
    out_df = out_df.applymap(subset=['combo'], func=color_combo)

    out_df = out_df.set_properties(**{'text-align': 'center'})
    # out_df.applymap(subset=['cnd_color' , 'thestrat_combo'], func=lambda v: "color:pink;" if v>4 else "color:darkblue;")
    # formatters = {c: '{:.2f}' for c in df.columns if c not in strat_cols}
    formatters = {c: '{:.2%}' for c in pct_cols}
    formatters['close'] = '${:.2f}'
    formatters['volume'] = lambda x: "{:.1f}M".format(x * 1e-6)
    formatters.update({c: '{:.1f}' for c in ["cci_14", "RSI14"]})
    out_df = out_df.format(formatters).hide_index()
    return out_df


def print_pct_html(df_index, df_stocks):
    out_df1 = print_apply_html_formats(df_index)
    print(out_df1.columns)
    out_df2 = print_apply_html_formats(df_stocks)
    # out_df1 = out_df1.set_caption()
    out_df1_html = out_df1.to_html(table_uuid="indexes")
    out_df2_html = out_df2.to_html(table_uuid="stocks")
    style = """
        * {font-family: sans-serif;}
        h1 {
        text-align: center;
        }
        main-cont{
        margin: auto;
        }
        table {
        border-collapse: collapse;
        width: 100%;
        font-size: 11pt;
        }
        .cont-img {
        height: 30px;
        width: 30px;
        background: white;
        display: flex;
        align-items: center;
        border-radius: 50%;
        }
        
        .ticker-img {
        max-height: 30px;
        max-width: 30px;
        border-radius: 50%;
        }
        table.dataTable thead th, table.dataTable thead td {
          padding: 3px 6px; !important
        }
        table.dataTable tbody th, table.dataTable tbody td{
            padding: 3px 6px; !important
        }
    """
    fg = get_fear_greed()
    if fg is not None:
        d_chg = fg['score'] / fg['previous_close'] - 1
        fg_str = f"""<span style="color:{get_color(fg['score'])};">{fg['rating'].capitalize()}, {round(fg['score'])} ({"+" if d_chg > 0 else ""}{d_chg :0.0%})</span>"""
    else:
        fg_str = ""
    with open(file_name, 'w', encoding="utf-8") as f:
        out = f"""
        <html><head>
        <title>Swing Screener</title>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
        <style>
        {style}
        </style>
        </head><body>
        <div class="main-cont">
        <h1>Swing Selected tickers, Relevant to: {datetime.now().strftime('%a, %B %d, %Y at %H:%M UTC')}</h1>
        <h3>Fear&Greed - {fg_str} </h3>
        {out_df1_html}
        {out_df2_html}
        <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <script>
            $(document).ready( function () {{
                $('#T_stocks').DataTable({{
                    // pageLength: 100,
                    paging: false,   
                    order: [[10, 'desc']],
                    // scrollY: 400,
                }});
            }});
        </script>
        </div>
        
        </body></html>
        """
        f.write(out)


def filter_nulls(data):
    null_tickers = data.isnull().sum(axis=0) != 0
    null_tickers = null_tickers[null_tickers].index.tolist()
    null_tickers = set([t[0] for t in null_tickers])
    if len(null_tickers):
        print('Couldnt fetch these tickers:', null_tickers)
        data = data.drop(columns=null_tickers)
    return data


def get_data_retry(tickers):
    data = get_daily_data(tickers, days_before=400, group_by='ticker')

    def _get_invalid_tickers(data):
        return [ticker for ticker in data.columns.get_level_values(0).unique()
                if data[ticker].iloc[-1].isna().any()]

    invalid_tickers = _get_invalid_tickers(data)
    tries = 0
    while len(invalid_tickers) and tries < 5:
        print(f'{len(invalid_tickers)=}, {tries=}, {invalid_tickers=}')
        missing_data = get_daily_data(invalid_tickers, days_before=0, group_by='ticker')
        data[invalid_tickers].iloc[-1] = missing_data.squeeze()
        invalid_tickers = _get_invalid_tickers(data)
        tries += 1
    # if data.iloc[-1].isna().all():
    #     data = data[:-1]
    #     print(f'Calculating for date: {data.index[-1].date()}')
    data.to_pickle("data_swing.pk")
    data = pd.read_pickle("data_swing.pk")
    return data


def get_swings():
    tickers = crypto + fintech + big_tech + semi + cyber + internet_software + saas + chinese + internet_retail + other + green + consumer + medical + customer_service + indexes
    tickers = high_growth + indexes + tickers
    tickers = list(set(tickers))

    data = get_data_retry(tickers)
    df = check_ticker(data)
    df_index = df.reindex(indexes)  # filter and reindex
    df_stocks = df[~df.index.isin(indexes)]
    # LONG - should be far from sma20, SHORT- higher than sma 20.
    # df_stocks = df_stocks.sort_values('sma20_pct', ascending=False)  # check long potentials
    df_stocks = df_stocks.sort_values(['sma20_pct', 'cnd_color', ], ascending=[False, True, ])  # check long potentials
    # CHECK RSI, and CCI, check also for volume decrease for sells.
    # check that close price is not far from open, look for doji, or bullish, also can use thestrat for indicator.
    # pprint_screener(df_stocks)

    print_pct_html(df_index, df_stocks)
    put_object_stocks(file_name, f'stocks/{file_name}')


def pprint_screener(df):
    df = df.copy()
    df['volume'] = df['volume'].apply(lambda x: f'{x / 1e6:0.1f}M')
    pct_cols = [c for c in df.columns if c.endswith('_pct')]
    df = df.sort_values('sma20_pct', ascending=False)
    df[pct_cols] = df[pct_cols].applymap(lambda x: f'{x:.2%}')
    # out_df = out_df.style.format({c: '{:.2%}' for c in pct_cols})
    # df = df.format()
    print(df)


def get_fear_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    try:
        res = requests.get(url, headers=headers).json()['fear_and_greed']
    except:
        return None
    return res


def get_color(x):
    if x > 70:
        return '#a50026'
    if x > 60:
        return '#d73027'
    if x < 30:
        return '#006837'
    if x < 40:
        return '#1a9850'
    return "Black"


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
    # get_fear_greed()
    get_swings()
