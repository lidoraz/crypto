url = 'https://tradingeconomics.com/calendar'

import requests
import pandas as pd
from bs4 import BeautifulSoup as bs


def _parse_cnt_price(val):
    multiplyer = {'K': 1e3, 'M': 1e6, 'B': 1e9}
    val = val.replace('$', '')
    last_char = val[-1]
    if last_char in multiplyer:
        # print(val[:-1])
        val = float(val[:-1]) * multiplyer[last_char]
    return val


def _parse_pct(val):
    val = val.replace('%', '')
    return float(val)


def parse(val):
    if '%' in val:
        return _parse_pct(val)
    else:
        return _parse_cnt_price(val)


def compare(val1, val2):
    val1 = parse(val1)
    val2 = parse(val2)
    return val1 > val2


headers = {
    'User-Agent': 'My User Agent 1.0',
    'From': 'youremail@domain.example',  # This is another valid field
    # 'cookie': 'calendar-countries=usa,tun; calendar-importance=3; ASP.NET_SessionId=d; cal-timezone-offset=180; TEServer=TEIIS'
    # ASP.NET_SessionId=pdl0gpiioeziec4ezsg5pgui
    # calendar-range=3;
    # WORKING
    'cookie': 'calendar-countries=usa, eu; calendar-importance=2; calendar-range=1;  TEServer=TEIIS'
    # last week: calendar-range=-2; ## THIS WEEK: calendar-range=3;
}


def strip_and_clean(x):
    x = x.getText().replace('\r\n', '').replace('\n', '').replace('®', '').strip()
    return ' '.join(x.split())


def scrape_data():
    r = requests.get(url, headers=headers)
    soup = bs(r.content)
    table = soup.find('table', {'id': 'calendar'})
    # cols = ['dt', 'country', 'title', 'actual', 'previous', 'consensus', 'forecast', 'compare']
    cols = ['importance', 'dt', 'country', 'title', 'actual', 'consensus', 'compare']
    res_lst = []
    for child in table.children:
        if isinstance(child, str):
            continue
        if child.get_attribute_list('class') == ['table-header']:
            #         print([strip_and_clean(x) for x in child.find_all(['th'])])
            date = strip_and_clean(child.find_all(['th'])[0])
        if child.has_attr('data-category'):
            entry = [strip_and_clean(x) for x in
                     child.find_all(['td'])]  # # [x for x in child.find_all(['td']) if x.attrs]
            try:
                importance = child.find_all(['td'])[0].contents[1].attrs['class'][0].split('-')[-1]
            except:
                print('importance extraction failed..')
                importance = 10
            time = entry[0]
            country = entry[1]
            title = entry[4]  # .strip()
            actual = entry[5]
            #         previous = entry[6]
            consensus = entry[7]
            #         forecast = entry[8]
            dt = pd.to_datetime(f'{date} {time}')
            # print(actual, consensus)
            _compare = None
            try:
                _compare = compare(actual, consensus) if len(actual) else None
            except Exception as e:
                print(f'Could not compare: {actual, consensus}', e)
            res = importance, dt, country, title, actual if len(actual) > 0 else 'NOTYET', consensus, _compare
            res_lst.append(res)
    #         print(','.join(res))
    #         print([strip_and_clean(x) for x in child.find_all(['td'])])
    df = pd.DataFrame(res_lst, columns=cols)
    return df
