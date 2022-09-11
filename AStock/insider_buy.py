import requests
import pandas as pd
from bs4 import BeautifulSoup

from AStock.sectors import get_daily_data


# from AStock.long_term_gaps import get_daily_data


def get_insiders():
    insider_url_group_buy_over100k = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=30&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=300&page=1"

    # insider_url_group_buy_and_sell_over100k = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=14&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=100&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    # not good as the filling date gets aggregated by last trade
    insider_url_group_buy_and_sell_over100k_last_week = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=7&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=100&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=100&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"

    res = requests.get(insider_url_group_buy_and_sell_over100k_last_week)
    soup = BeautifulSoup(res.text, 'html.parser')

    table = soup.find('table', {'class': 'tinytable'})
    table = str(table).replace(u'\xa0', u' ')
    df_i = pd.read_html(str(table))[0]
    # print(df_i.head())
    return df_i


def filter_stocks(df_i, avg_volume_m=2, minimum_price=10):
    # filter to get out penny stocks with no volume,
    # more chance for institutional traders to buy and get it to the moon
    avg_volume_m = avg_volume_m * 1e6
    tickers = df_i.Ticker.to_list()
    if avg_volume_m is not None:
        daily_volume = get_daily_data(tickers, days_before=60, group_by='column')['Volume']
        avg_volume = daily_volume.rolling(20).mean().iloc[-1].rename('avg_volume')
        df_i = df_i.merge(avg_volume, left_on='Ticker', right_on=avg_volume.index)
        df_i = df_i[df_i['avg_volume'] > avg_volume_m]
        df_i['avg_volume'] = ((df_i['avg_volume'] / 1e6).round(1))
    if minimum_price is not None:
        price = df_i['Price'].str.replace('$', '').apply(float)
        price_cond = price > minimum_price
        df_i = df_i[price_cond]
    # filtered_tickers = avg_volume[avg_volume > avg_volume_m]
    # df_i = df_i[df_i['Ticker'].isin(filtered_tickers.index)]
    return df_i


def run():
    df_i = get_insiders()
    df_i = filter_stocks(df_i, avg_volume_m=2, minimum_price=5)
    display(df_i)


def display(df_i):
    # 'Owned',
    columns = ['Trade Date', 'Ticker', 'Ins', 'Price', 'Qty', 'ΔOwn', 'Value', 'avg_volume']
    type_col = 'Trade Type'
    is_buy = df_i['Trade Type'].str.slice(0, 1) == 'P'  # P - Purchase
    is_sell = df_i['Trade Type'] == 'S - Sale'
    is_oe = df_i['Trade Type'] == 'S - Sale+OE'

    print('-> Buy')
    print(df_i[is_buy][columns])
    print('-> Sale')
    print(df_i[is_sell][columns])
    print('-> Sale + Option exercise ')
    print(df_i[is_oe][columns])

if __name__ == '__main__':
    run()
