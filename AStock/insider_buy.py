import requests
import pandas as pd
from bs4 import BeautifulSoup

from AStock.sectors import get_daily_data
from Indicators.Indicator import human_format
from datetime import datetime

# from AStock.long_term_gaps import get_daily_data

google_analytics = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Y093DMFS92"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-Y093DMFS92');
</script>
"""


def get_insiders():
    insider_url_group_buy_over100k = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=30&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=300&page=1"

    # insider_url_group_buy_and_sell_over100k = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=14&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=100&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    # not good as the filling date gets aggregated by last trade
    insider_url_group_buy_and_sell_over100k_last_week = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=7&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=100&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    print('Getting Data from relevant to last week')
    res = requests.get(insider_url_group_buy_and_sell_over100k_last_week)
    soup = BeautifulSoup(res.text, 'html.parser')

    table = soup.find('table', {'class': 'tinytable'})
    table = str(table).replace(u'\xa0', u' ')
    df_i = pd.read_html(str(table))[0]
    # print(df_i.head())
    return df_i


def filter_stocks(df, avg_volume_m=2, minimum_price=10):
    # filter out penny stocks with no volume,
    # more chance for institutional traders to buy and get it to the moon
    avg_volume_m = avg_volume_m * 1e6
    tickers = df.Ticker.to_list()
    if avg_volume_m is not None:
        daily_volume = get_daily_data(tickers, days_before=60, group_by='column')['Volume']
        avg_volume = daily_volume.rolling(20).mean().iloc[-1].rename('Vol')
        df = df.merge(avg_volume, left_on='Ticker', right_on=avg_volume.index)
        df = df[df['Vol'] > avg_volume_m]
        df['Vol'] = ((df['Vol'] / 1e6).round(1))
    if minimum_price is not None:
        price = df['Price'].str.slice(1).str.replace(",", "").apply(float)
        price_cond = price > minimum_price
        df = df[price_cond]
    # filtered_tickers = avg_volume[avg_volume > avg_volume_m]
    # df_i = df_i[df_i['Ticker'].isin(filtered_tickers.index)]
    return df


def get_header(title, color, h_num=2):
    return f'<h{h_num} style="background-color: {color}; padding:10px; text-align: center; border: solid 2px black;">{title}</h{h_num}>'


def _get_days_ago(series):
    map_days = lambda x: 'Today' if x == 0 else f'{x} days' if x > 1 else f'{x} day'
    return (datetime.now() - pd.to_datetime(series)).dt.days.apply(map_days)


def color_by_cell(df, col, cmap):
    if not len(df):
        return df.style.hide_index()

    def ins_f(ins):
        ins = int(ins)
        sev = f"({'$' * ins})" if ins > 1 else ''
        return f'{sev} {ins}'

    df['Trade'] = _get_days_ago(df['Trade'])
    df['Filing'] = _get_days_ago(df['Filing'])

    df['Ins'] = df.apply(
        lambda x: f"""<a target=_blank href="http://openinsider.com/{x['Ticker']}">{ins_f(x['Ins'])}</a>""", axis=1)

    s = df.style.background_gradient(axis=0, gmap=df[col], cmap=cmap) \
        .format(formatter={'Value': lambda x: f"${int(x):,.0f}",
                           'Vol': lambda x: f'{x:.2f}M',
                           'Qty': lambda x: f"{human_format(int(x))}",
                           'Ticker': lambda x: get_link(x)}) \
        .hide(axis='index')
    # .hide(axis="index")
    # .set_properties(**{'padding': '5px', 'font-size': '12pt', 'font-family': 'sans-serif', 'font-weight': '500'})
    return s


def get_link(t):
    return f'<a target=_blank href="https://finviz.com/quote.ashx?t={t.upper()}" alt="Finviz">{t}</a>'


style = """
<style> 
* {font-family: sans-serif; color:white;}
h1, h2, h3, h4, h5, h6 {margin:3px; padding:3px;}
a {
color: black;
}
body {
background: rgb(2,0,36);
background: linear-gradient(270deg, rgba(2,0,36,1) 0%, rgba(9,9,121,1) 100%, rgba(0,212,255,1) 100%); 
}

.cont-img {
height: 35px;
width: 35px;
background: white;
display: flex;
align-items: center;
border-radius: 50%;
}

.ticker-img {
max-height: 35px;
max-width: 35px;
border-radius: 50%;
}

table {
border-collapse: collapse;
width: 100%;
}
.main-cont{
    margin: auto;
    background-color: black;
}

.main-cont tr td{
padding: 5px;
font-size: 16pt; 
font-family: sans-serif;
font-weight: 500;
text-align: center;
}
a:link {
  color: inherit;
  -webkit-text-fill-color: inherit;
}

@media only screen and (min-width:1000px) {
    .main-cont{
        width:812px;
    }
    .main-cont tr td{
        font-size: 12pt;
    }
}
</style>
"""


def create_html(df):
    def _sort_df(df):
        return df.sort_values('Filing', ascending=False).reset_index(drop=True)

    # df.rename(columns={"ΔOwn": "±ΔOwn"})
    columns = ['Filing Date', 'Trade Date', 'img', 'Ticker', 'Ins', 'Price', 'Qty', 'ΔOwn', 'Value', 'Vol']
    is_buy = df['Trade Type'].str.slice(0, 1) == 'P'  # P - Purchase
    is_sell = df['Trade Type'] == 'S - Sale'
    is_oe = df['Trade Type'] == 'S - Sale+OE'

    df = df[columns]
    df = df.rename(columns={"Trade Date": "Trade",
                            "Filing Date": "Filing",
                            "img": "",
                            "ΔOwn": "±Own"})
    df_1 = color_by_cell(_sort_df(df[is_buy]), 'Value', 'Greens')
    df_2 = color_by_cell(_sort_df(df[is_sell]), 'Value', 'Reds')
    df_3 = color_by_cell(_sort_df(df[is_oe]), 'Value', 'Oranges')
    with open('daily_insider.html', 'w', encoding="utf-8") as f:
        f.write("<html><head><title>Insider Transactions</title>")
        f.write('<meta charset="UTF-8">\n')
        f.write(google_analytics)
        f.write(style)
        f.write("</head>")
        f.write('<h1> מה נשמע?? </h1>')
        f.write('<div class="main-cont">')
        f.write("<h1> Insider Transactions, past week </h1>")
        f.write(
            f"<h6> from openinsider.com, Updated to: {datetime.now(tz=None).strftime('%a, %B %d, %Y at %H:%M UTC')} </h6>")
        f.write(get_header(" -> Insider Buy ", "#21421e", h_num=2))
        f.write(df_1.to_html())
        f.write(get_header(" -> Insider Sale ", "#801818", h_num=2))
        f.write(df_2.to_html())
        f.write(get_header(" -> Insider Sale + Option exercise ", "#e9692c", h_num=2))
        f.write(df_3.to_html())
        f.write('</div></html>')


def get_ticker_img(ticker):
    ticker = ticker.upper()
    path = f"https://financialmodelingprep.com/image-stock/{ticker}.png"
    # <a  target=_blank href="http://openinsider.com/{x}">{x}</a>
    html_img = f"""<div class="cont-img"><img src="{path}" class="ticker-img"/> </div>"""
    return html_img


def preprocess(df):
    df['Value'] = df['Value'].str.replace(',', "").str.extract("(\d+)")
    df['Filing Date'] = pd.to_datetime(df['Filing Date'])
    df['Trade Date'] = pd.to_datetime(df['Trade Date'])
    df['img'] = df['Ticker'].apply(get_ticker_img)
    return df


def put_object_stocks(path_from, path_to):
    BUCKET_NAME = 'all-finance-data'
    import boto3
    s3 = boto3.client("s3")
    with open(path_from, 'r') as f:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=path_to,
            Body=f.read(),
            CacheControl="max-age=0,no-cache,no-store,must-revalidate",
            ContentType="text/html; charset=utf-8",
            ACL="public-read"
        )
    # buck = s3.Bucket(BUCKET_NAME)
    print(f"Uploading file:: {path_from} bucket: {BUCKET_NAME}/{path_to}")
    # buck.upload_file(path_from, path_to)


def run(minimum_price=5, avg_volume_m=2):
    df = get_insiders()
    df = filter_stocks(df, avg_volume_m=avg_volume_m, minimum_price=minimum_price)
    df.to_pickle('tmp.pk')
    df = pd.read_pickle('tmp.pk')
    df = preprocess(df)
    create_html(df)
    put_object_stocks('daily_insider.html', 'stocks/daily_insider.html')


# def display(df):
#     # 'Owned',
#     columns = ['Trade Date', 'Ticker', 'Ins', 'Price', 'Qty', 'ΔOwn', 'Value', 'Vol']
#     type_col = 'Trade Type'
#     is_buy = df['Trade Type'].str.slice(0, 1) == 'P'  # P - Purchase
#     is_sell = df['Trade Type'] == 'S - Sale'
#     is_oe = df['Trade Type'] == 'S - Sale+OE'
#     df['Trade Date'] = pd.to_datetime(df['Trade Date'])
#
#     def _sort_df(df):
#         return df.sort_values('Trade Date', ascending=False)
#
#     print('-> Buy')
#     print(_sort_df(df[is_buy][columns]))
#     print('-> Sale')
#     print(_sort_df(df[is_sell][columns]))
#     print('-> Sale + Option exercise ')
#     print(_sort_df(df[is_oe][columns]))


if __name__ == '__main__':
    run()
