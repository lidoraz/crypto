import pandas as pd
from datetime import datetime

from AStock.insider_buy import put_object_stocks, google_analytics, get_link
from Indicators import RSI, TheStratInd
import requests
import matplotlib
import base64
from tqdm import tqdm

matplotlib.use('Agg')
import matplotlib.pyplot as plt

file_name_1 = 'daily_swing.html'
file_name_2 = 'daily_swing_big.html'
icon_url = "https://static.stocktitan.net/company-logo/{}.png"
# icon_url = "https://companiesmarketcap.com/img/company-logos/32/{}.png"

finviz_valuation_url = "https://finviz.com/screener.ashx?v=121&o=-forwardpe&t={}"

WITH_AFTER_HOURS = True
high_growth = ['AFRM', 'AMD', 'CFLT', 'CRWD', 'DDOG', 'DLO', 'GLBE', 'GTLB', 'MELI', 'NET', 'NVDA',
               'OKTA', 'OPEN', 'RBLX', 'S', 'SHOP', 'SNOW', 'SOFI', 'TOST', 'TSLA', 'TWLO', 'ZI', 'WOLF', 'SOXX',
               'ARKK',
               'MNDY', 'BILL', 'ENPH', 'ASAN', 'ESTC', 'TEAM', 'IOT', 'HCP', 'ZS', 'U', 'MDB', 'SEDG', 'DAVA',
               'ENTG', 'FSLR', 'GLOB', 'PLTR', 'TTD', 'HUBS', 'NOW', 'PATH', 'PCOR', 'EPAM', 'PAYC', 'FIVN', 'CYBR',
               'DT', 'FTNT', 'PCTY', 'APP', 'PANW', 'PAGS']
crypto = ['MARA', 'HUT', 'MSTR', 'RIOT', 'COIN']
# FILTER GROWTH VS VALUE STOCK
fintech = ['AFRM', 'SOFI', 'PYPL', 'SQ', 'UPST', 'LMND']
big_tech = ['TSLA', 'AAPL', 'MSFT', 'GOOGL']
semi = ['NVDA', 'AMD', 'MU', 'TXN', 'TSM', 'ASML', 'AMAT']
cyber = ['CRWD', 'S', 'PANW', 'CYBR']
saas = ['MNDY', 'DDOG', 'DASH', 'PATH', 'SNOW', 'CRM', 'VEEV']
internet_software = ['META', 'GOOGL', 'PINS', 'ADBE']
chinese = ['BABA', 'NIO', 'JD', ]
other = ['RBLX', 'ROKU', 'DIS', 'NFLX', 'BA', "ZIM", "GS", "SCHW"]
green = ['SEDG', 'ENPH']
consumer = ['AMZN', 'SHOP', 'CHWY', 'RIVN', 'LULU']
internet_retail = ['AMZN', 'CHWY', 'LULU', 'SHOP', 'ETSY']

medical = ['TDOC', 'MRNA', "JNJ"]
indexes = ['SPY', 'QQQ', 'IWM', 'DIA']  # 'RTY=F'
customer_service = ['WING', 'CROX', 'LOVE', 'UBER']
tw_icons_path = "https://s3-symbol-logo.tradingview.com/sector/"
# technology--big.svg" for bigger icons
sector_indexes = {"XLK": f"{tw_icons_path}technology--big.svg",
                  "XLC": f"{tw_icons_path}communication-services--big.svg",
                  "XLU": f"{tw_icons_path}utilities--big.svg",
                  "XLRE": f"{tw_icons_path}real-estate--big.svg",
                  "XLB": f"{tw_icons_path}materials--big.svg",
                  "XLP": f"{tw_icons_path}consumer-staples--big.svg",
                  "XLI": f"{tw_icons_path}industrial--big.svg",
                  "XLY": f"{tw_icons_path}consumer-discretionary--big.svg",
                  "XLV": f"{tw_icons_path}health-care--big.svg",
                  "XLE": f"{tw_icons_path}energy--big.svg",
                  "XLF": f"{tw_icons_path}financial--big.svg"}

# ADD VIX TICKERS FOR BAROMETER: ^VIX, ^VIX9D, ^VIX3M
# all_etf_longname

style = """
        * {font-family: sans-serif;}
        h1 {
        text-align: center;
        }
        .main-cont{
        max-width: 900px;
        margin: auto;
        }
        table {
        border-collapse: collapse;
        width: 100%;
        font-size: 11pt;
        }
        .cont-img {
        height: 27px;
        width: 27px;
        background: white;
        display: flex;
        align-items: center;
        border-radius: 50%;
        }

        .ticker-img {
        max-height: 27px;
        max-width: 27px;
        border-radius: 50%;
        }
        table.dataTable thead th, table.dataTable thead td {
          padding: 3px 6px; !important
        }
        table.dataTable tbody th, table.dataTable tbody td{
            padding: 3px 6px; !important
        }
        #T_stocks thead th{
          position: sticky;
          top: 0;
          background-color: white;
          background-repeat: no-repeat;
        }
        #T_stocks_filter{
            float: left;
        }
        a {
          color: inherit; /* blue colors for links too */
          text-decoration: inherit; /* no underline */
        }
    """


def check_ticker(data, day_shift=1, minimum_volume=1e6 / 2):
    print('Relative to date: ', data.index[-day_shift].date())
    tickers = set([x[0] for x in data.columns.tolist()])

    # print(len(data))

    def change_pct(new, old):
        return new / old - 1

    def add_sma_pct(close, len):
        return change_pct(close.rolling(len).mean(), close).rename(f'sma{len}_pct')

    res = pd.DataFrame()

    def volume_thumbnail(df_t, lk):
        lat_df = df_t[-lk:]
        color_bars = ['green' if x['close'] > x['open'] else 'red' for _, x in lat_df.iterrows()]
        plt.bar(range(lk), lat_df['volume'], color=color_bars)
        plt.axis('off')
        plt.savefig(f'AStock/img/{ticker}.png', bbox_inches='tight')
        plt.clf()

    for ticker in tqdm(tickers):
        if ticker == 'XLE':
            print()
        df_t = data[ticker]
        df_t.columns = [c.lower() for c in df_t.columns]
        na_rows = df_t.isna()['close'].sum(axis=0)
        if na_rows > 0:
            print(f"{ticker=} has {na_rows=} !")
        df_t = df_t.ffill()
        # minimum volume req:
        if df_t['volume'][-14:].rolling(14).mean()[-1] < minimum_volume:
            print(f'Filtered out ticker: {ticker} due to low avg volume')
            continue

        def sub_dates_closest(df, days_back):
            for delta in range(7):
                index = df.index[-1] - pd.to_timedelta(f"{days_back + delta}D")
                if index in df.index:
                    return df.loc[index]

        price = df_t['close'].iloc[-1]
        ytd_date = pd.to_datetime(f"{datetime.today().year}-01-01")
        pct_values = {"D_chg_pct": price / sub_dates_closest(df_t, 1)['close'] - 1,
                      "W_chg_pct": price / sub_dates_closest(df_t, 7)['close'] - 1,
                      "2W_chg_pct": price / sub_dates_closest(df_t, 14)['close'] - 1,
                      "M_chg_pct": price / sub_dates_closest(df_t, 30)['close'] - 1,
                      "Q_chg_pct": price / sub_dates_closest(df_t, 90)['close'] - 1,
                      "YTD_chg_pct": price / sub_dates_closest(df_t, (datetime.today() - ytd_date).days)['close'] - 1,
                      "Y_chg_pct": price / sub_dates_closest(df_t, 365)['close'] - 1,
                      "2Y_chg_pct": price / sub_dates_closest(df_t, 720)['close'] - 1}
        sma_lookback = [20, 50, 150, 200]
        ind_sma = {f'sma{x}_pct': add_sma_pct(df_t[-x:]['close'].dropna(), x).iloc[-1] for x in sma_lookback}
        ind_momentum = {
            'CCI20': add_cci(df_t[-20:], 20).iloc[-1],
            'RSI14': RSI(14).calc(df_t[-70:]).iloc[-1].squeeze(),
            **TheStratInd(False).calc(df_t[-5:]).fillna('').iloc[-1].to_dict()
        }
        price_volume = df_t['volume'].iloc[-1] * df_t['close'].iloc[-1]

        signals = {"Price": price,
                   **pct_values,
                   **ind_sma,
                   **ind_momentum,
                   "Volume": df_t['volume'].iloc[-1],
                   "Vol($)": price_volume
                   }
        # dist to sma, if below, will be positive, if above, should be negative
        volume_thumbnail(df_t, 5)
        curr_row = pd.Series(signals, name=ticker)
        # curr_row = df_t.iloc[-day_shift].rename(ticker)
        # curr_row = curr_row.drop(['adj close', 'open', 'high', 'low'])  # 'High', 'Low'
        with open(f'AStock/img/{ticker}.png', 'rb') as f:
            b64 = base64.b64encode(open(f'AStock/img/{ticker}.png', 'rb').read()).decode("utf-8")
            src_b64 = f"data: image/png; base64,{b64}"
            curr_row['profile_volume'] = f'<img src="{src_b64}" loading="lazy" height="27px"/>'
        # curr_row['profile_volume'] = f'<img src="img/{ticker}.png" height="27px"/>'
        res = pd.concat([res, curr_row.to_frame()], axis=1)
    res = res.T
    return res


def add_cci(ohlc, length):
    src = ohlc[['high', 'low', 'close']].sum(axis=1) / 3
    ma = ohlc['close'].rolling(length).mean()
    dev = ohlc['close'].rolling(length).std()
    cci = (src - ma) / (0.015 * dev)
    return pd.Series(cci).rename(f'CCI{length}').round(2)


def print_apply_html_formats(df, cols, pct_mul=1, custom_icons=None):
    df.columns = [c.replace("thestrat_", "") for c in df.columns]
    df.columns = [c.replace("_chg_pct", "") for c in df.columns]
    df.columns = [c.replace("_pct", "") for c in df.columns]
    pct_cols = {"D": 0.08, "W": 0.15, "2W": 0.15, "M": 0.2, "Q": 0.25, "YTD": 0.25, "Y": 0.5, "2Y": 0.5, "sma20": 0.1, "sma50": 0.15,
                "sma150": 0.2, "sma200": 0.3}
    mapper = {"Hammer": "🔨", "Shooter": "🔫"}
    df['cnd_type'] = df['cnd_type'].apply(lambda x: mapper.get(x, ""))
    df['Ticker'] = df.index.values
    if custom_icons:
        img_ticker_s = '<div class="cont-img"> <img src="{}" loading="lazy" class="ticker-img" /></div>'
        df[' '] = df['Ticker'].apply(lambda x: img_ticker_s.format(sector_indexes[x]))
    else:
        img_ticker_s = f'<div class="cont-img"> <img src={icon_url} loading="lazy" class="ticker-img" /></div>'
        df[' '] = df['Ticker'].apply(lambda x: img_ticker_s.format(x.upper()))
    df['Ticker'] = df['Ticker'].apply(get_link)
    df = df.rename(columns={"cnd_color": "c", "cnd_type": "t", "profile_volume": "Vol", "index": "Ticker"})
    df = df[cols]
    out_df = df.style
    for pct_col, vmax in pct_cols.items():
        vmax *= pct_mul
        out_df = out_df.background_gradient(subset=pct_col, cmap='RdYlGn', axis=0, vmin=-vmax,
                                            vmax=vmax) if pct_col in cols else out_df
    # out_df = out_df.background_gradient(subset="CCI20", cmap='RdYlGn_r', vmin=-101, vmax=101, axis=0)
    out_df = out_df.background_gradient(subset='RSI14', cmap='RdYlGn_r', vmin=30, vmax=70, axis=0)
    out_df = out_df.applymap(subset=['combo'], func=color_combo) if 'combo' in cols else out_df
    out_df = out_df.set_properties(**{'text-align': 'center'})
    # out_df.applymap(subset=['cnd_color' , 'thestrat_combo'], func=lambda v: "color:pink;" if v>4 else "color:darkblue;")
    # formatters = {c: '{:.2f}' for c in df.columns if c not in strat_cols}
    formatters = {c: '{:.1%}' for c in pct_cols}
    formatters['Price'] = '${:.2f}'
    fun_vol = lambda x: round(x * 1e-6, 1)
    formatters['Vol($)'] = fun_vol  # lambda x: "{:.1f}M".format(x * 1e-6)
    formatters['Volume'] = fun_vol  # lambda x: "{:.1f}M".format(x * 1e-6)
    formatters.update({c: '{:.1f}' for c in ["RSI14"]})
    # formatters.update({c: '{:.1f}' for c in ["CCI20", "RSI14"]})
    out_df = out_df.format(formatters).hide_index()
    return out_df


def print_pct_html(df_index, df_sectors, df_stocks, cols, file_name):
    out_df1 = print_apply_html_formats(df_index, cols, 0.2)
    out_df2 = print_apply_html_formats(df_stocks, cols, 1.0)
    out_df3 = print_apply_html_formats(df_sectors, cols, 0.4, custom_icons=sector_indexes)
    # out_df1 = out_df1.set_caption()
    out_df1_html = out_df1.to_html(table_uuid="indexes")
    out_df2_html = out_df2.to_html(table_uuid="stocks")
    out_df3_html = out_df3.to_html(table_uuid="sectors")
    finviz_valuation_link = finviz_valuation_url.format(','.join(df_stocks.index.to_list()))
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
        <link rel="icon" type="image/x-icon" href="favicon.ico">
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
        {google_analytics}
        <style>
        {style}
        </style>
        </head><body>
        <div class="main-cont">
        <h1>Swing Selected tickers</h1>
        <h4>Fear&Greed - {fg_str} <span style="float: right;"><a href={finviz_valuation_link}>Valuation Screener✓</a>, Data Relevant to: {datetime.now().strftime('%a, %B %d, %Y at %H:%M UTC')}</span><a href="daily_insider.html">Insider✓</a></h4>
        <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <!-- <h3>Indexes</h3> -->
        {out_df1_html}
        <!-- <h3>Sectors</h3> -->
        {out_df3_html}
        <script>
            $(document).ready( function () {{
                $('#T_sectors').DataTable({{
                    searching: false,
                    info: false,
                    fixedHeader: true, // not working, fixed with sticky header
                    paging: false,   
                    order: [[{cols.index('D')}, 'desc']],
                    // scrollY: 400,
                }});
            }});
        </script>
        <!-- <h3>Stocks</h3> -->
        {out_df2_html}
        <script>
            $(document).ready( function () {{
                $('#T_stocks').DataTable({{
                    // pageLength: 100,
                    fixedHeader: true, // not working, fixed with sticky header
                    paging: false,
                    order: [[{cols.index('sma20')}, 'desc']],
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
    import yfinance as yf

    def _get_daily_data(tickers, period):
        return yf.download(' '.join(tickers), period=period,
                           rounding=True,
                           prepost=WITH_AFTER_HOURS,
                           group_by='ticker',  # default is on columns. ticker is easier to iterate
                           auto_adjust=False,  # false on default, what does it do?
                           show_errors=True,
                           interval='1d', threads=True, progress=True)

    data = _get_daily_data(tickers, '2y')

    def _get_invalid_tickers(data):
        return [ticker for ticker in data.columns.get_level_values(0).unique()
                if data[ticker].iloc[-1].isna().any()]

    if len(tickers) == 1:
        return data
    invalid_tickers = _get_invalid_tickers(data)
    tries = 0
    while len(invalid_tickers) and tries < 5:
        print(f'{len(invalid_tickers)=}, {tries=}, {invalid_tickers=}')
        missing_data = _get_daily_data(invalid_tickers, '1d')
        data[invalid_tickers].iloc[-1] = missing_data.squeeze()
        invalid_tickers = _get_invalid_tickers(data)
        tries += 1
    # if data.iloc[-1].isna().all():
    #     data = data[:-1]
    #     print(f'Calculating for date: {data.index[-1].date()}')
    return data


def build(df_index, df_sectors, df_stocks):
    cols = ['Ticker', ' ', 'Price', 'D', 'W', 'M', 'Q', 'YTD', 'Y', 'sma20', 'sma50', 'sma200', 'RSI14',
            'Vol']
    print_pct_html(df_index, df_sectors, df_stocks, cols, file_name_1)
    put_object_stocks(file_name_1, f'stocks/{file_name_1}')


def build_big(df_index, df_sectors, df_stocks):
    cols_big = ['Ticker', ' ', 'Price', 'Vol', 'D', 'W', '2W', 'M', 'Q', 'YTD', 'Y', '2Y', 'sma20', 'sma50', 'sma150',
                'sma200',
                'CCI20', 'RSI14', 'num', 'c', 't', 'combo', 'Volume', "Vol($)"]
    print_pct_html(df_index, df_sectors, df_stocks, cols_big, file_name_2)
    put_object_stocks(file_name_2, f'stocks/{file_name_2}')


def get_swings(test=False):
    tickers = crypto + fintech + big_tech + semi + cyber + internet_software + saas + chinese + internet_retail + other + green + consumer + medical + customer_service + indexes
    sector_tickers = list(sector_indexes.keys())
    tickers += high_growth + indexes + sector_tickers
    tickers = list(set(tickers))

    data = get_data_retry(tickers)
    df = check_ticker(data)
    df.to_pickle("data_swing.pk")
    df = pd.read_pickle("data_swing.pk")

    df_index = df.reindex(indexes)  # filter and reindex
    df_sectors = df.loc[sector_tickers]
    df_stocks = df[~df.index.isin(sector_tickers + indexes)]
    # LONG - should be far from sma20, SHORT- higher than sma 20.
    # df_stocks = df_stocks.sort_values('sma20_pct', ascending=False)  # check long potentials
    # df_stocks = df_stocks.sort_values(['sma20_pct', 'cnd_color', ], ascending=[False, True, ])  # check long potentials
    # CHECK RSI, and CCI, check also for volume decrease for sells.
    # check that close price is not far from open, look for doji, or bullish, also can use thestrat for indicator.
    # pprint_screener(df_stocks)
    build(df_index, df_sectors, df_stocks)
    build_big(df_index, df_sectors, df_stocks)


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
