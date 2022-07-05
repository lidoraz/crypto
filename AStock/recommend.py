import yfinance as yf
import pandas as pd
import time
import os

# snow = yf.Ticker('SNOW')

# print(snow.calendar) # can be multiple use snow.calendar[0]
# print(snow.calendar)
# print('snow.recommendations')  # JP Morgan seems to have high impcact
# print(snow.recommendations)  # filter to curr date, then group by, and take value counts over to grade
# (To Grade) -> Buy, Overweight, Outperform, Hold, Market Outperform,

# ['Buy', 'Neutral', 'Outperform', 'Hold', 'Underweight', 'Underperform', 'Sell', 'Overweight', 'Equal-Weight', 'Sector Perform',
# 'Market Perform', 'Market Outperform', '', 'In-Line', 'Perform', 'Sector Weight', 'Underperformer', 'Peer Perform']

# ['Buy', 'Neutral', 'Outperform', 'Hold', 'Underweight', 'Underperform', 'Sell', 'Overweight',
# 'Equal-Weight', 'Sector Perform', 'Market Perform', 'Market Outperform', '', 'In-Line', 'Perform', 'Sector Weight', 'Underperformer', 'Peer Perform']

# Maybe use this convertor when we have multiple recommendations
grade_to_value = {'Buy': 2,
                  'Neutral': 0,
                  'Outperform': 3,
                  'Hold': 0,
                  'Underweight': -3,
                  'Underperform': -3,
                  'Sell': -2,
                  'Overweight': 3,
                  'Equal-Weight': 0,
                  'Sector Perform': 1,
                  'Market Perform': 1,
                  'Market Outperform': 3,
                  '': 0,
                  'In-Line': 0,
                  'Perform': 1,
                  'Sector Weight': 0,
                  'Underperformer': -3,
                  'Peer Perform': 0}


# ['Buy', 'Overweight', 'Hold', 'Outperform', 'Neutral', 'Equal-Weight', 'Market Outperform', 'Sell', 'Market Perform', 'Underweight']
# snow.recommendations[snow.recommendations.index.date == pd.to_datetime('2022-05-26')]['To Grade'].value_counts()
# snow.recommendations[snow.recommendations.index.date == '2022-05-26']
# print('snow.analysis')


# # Contains company estimatin for the future, current Q, Next Q, end of the year, and 5 years from now.
# in terms of groth, earnings, eps, revenue
# print(snow.analysis)


def get_earnings(ticker, curr_dt):
    # Sometimes its a df of one row, or more.
    # https://finance.yahoo.com/quote/GOOG, uses earning from table
    cal = ticker.calendar
    if cal is None:
        return None
    cal = cal.T
    if len(cal) == 0:
        return None
    col = 'Earnings Date'
    next_earnings = cal.sort_values(col).iloc[-1].to_dict()
    next_earnings_date = next_earnings[col].date()
    # keys ['Earnings Date', 'Earnings Average', 'Earnings Low', 'Earnings High', 'Revenue Average', 'Revenue Low', 'Revenue High']
    # TODO: Test what happens when there is earnings.
    # print('Earning date: next_earnings_date')
    if curr_dt.date() > next_earnings_date:
        return None
    return next_earnings_date
    # if curr_date = next earning -> do it.


def get_recommendations(ticker, curr_dt, delta='7D'):
    # Use trusted Firms
    delta = pd.to_timedelta(delta)
    limit = 3
    trusted_firms = ['JP Morgan', 'Morgan Stanley']
    # cols = ['Firm', 'To Grade']
    # rec_values = rec[rec.index.date == curr_dt.date()] # ['To Grade'].value_counts()
    rec = ticker.recommendations
    if rec is None or len(rec) == 0:
        return None
    rec = rec[rec.index.date > curr_dt.date() - delta].sort_index(ascending=False)[:limit]
    dates = rec.index.to_list()
    firms = rec['Firm'].to_list()
    to_grades = rec['To Grade'].to_list()
    if len(dates) == 0:
        return None
    return list(zip(firms, to_grades, dates))

publishers = {}
def add_or_increment(k):
    key = publishers.get(k, None)
    if key is None:
        publishers[k] = 1
    else:
        publishers[k] = publishers[k] + 1


def get_news(ticker, curr_dt):
    # uuid, title, publisher, link, 'providerPublishTime', 'type'
    recent_news = []
    try:
        for story in ticker.news:
            story['providerPublishTime'] = pd.to_datetime(story['providerPublishTime'], unit='s')
            dt = pd.to_datetime(story['providerPublishTime'], unit='s')
            if curr_dt.date() > (dt + pd.to_timedelta('7D')).date():
                continue
            recent_news.append(dict(dt=dt,
                                    title=story['title'],
                                    relatedTickers=story['relatedTickers'],
                                    publisher=story['publisher'],
                                    type=story['type'],
                                    link=story['link']))
    except Exception as e:
        print('got exception: at news:', e)

    return recent_news


def get_info(symbol, curr_dt):
    ticker = yf.Ticker(symbol)
    next_earnings_date = get_earnings(ticker, curr_dt)
    if next_earnings_date and next_earnings_date == curr_dt.date():
        print(f'Ticker: {ticker}, Today is earning date!')
    rec_values = get_recommendations(ticker, curr_dt)
    if rec_values is not None and rec_values[0][2].date() == curr_dt.date():
        print(f'Ticker: {ticker}, Today has new recommendation! {rec_values[0]}')
    news = get_news(ticker, curr_dt)
    res = dict(earnings=next_earnings_date, recommendations=rec_values, news=news)

    time.sleep(0.01)
    return res


def add_info_symbols(symbols, curr_dt, threaded=True):
    res_ = []
    if threaded:
        from multiprocessing import Pool
        with Pool(os.cpu_count()) as p:
            results = p.starmap(get_info, [(symbol, curr_dt) for symbol in symbols])
    else:
        results = [get_info(symbol, curr_dt) for symbol in symbols]
    for idx, symbol in enumerate(symbols):
        res = results[idx]
        res['symbol'] = symbol
        res_.append(res)
        print(symbol, res)
        for story in res['news']:
            add_or_increment(story['publisher'])

    print('Publishers:', {k: v for k, v in reversed(sorted(publishers.items(), key=lambda item: item[1]))})
    return pd.DataFrame(res_)


if __name__ == '__main__':
    add_info_symbols(['NFLX', 'AAPL', 'SNOW'], pd.to_datetime('2022-06-23'), False)