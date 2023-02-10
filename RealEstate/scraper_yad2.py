import numpy as np
import requests
import schedule
from tqdm import tqdm
import time
import pandas as pd
from datetime import datetime
import sqlite3

import sqlalchemy

history_dtype = {
    "price": sqlalchemy.Integer,
    "processing_date": sqlalchemy.Date
}

url_forsale_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
TRIES = 5
redundant_cols = ['images', 'default_layout', 'can_change_layout', 'ad_type', 'IsVisibleForReco',
                  'can_hide', 'external', 'is_hidden', 'is_liked', 'is_trade_in_button',
                  'like_count', 'line_1_text_color', 'line_2_text_color', 'remove_on_unlike', 'type',
                  'uid', 'priority', 'background_type', 'title', 'row_5', 'deal_info', 'currency_text',
                  'mp4_video_url', 'broker_avatar']

today_cols = ['line_1', 'line_2', 'line_3', 'row_1', 'row_2', 'row_3', 'row_4',
       'search_text', 'title_1', 'title_2', 'images_count', 'img_url',
       'images_urls', 'video_url', 'primaryarea', 'primaryareaid',
       'areaid_text', 'secondaryarea', 'area_id', 'city', 'city_code',
       'street', 'coordinates', 'geohash', 'ad_highlight_type',
       'background_color', 'highlight_text', 'order_type_id', 'ad_number',
       'cat_id', 'customer_id', 'feed_source', 'id', 'link_token', 'merchant',
       'contact_name', 'merchant_name', 'record_id', 'subcat_id', 'currency',
       'price', 'date', 'date_added', 'updated_at', 'promotional_ad',
       'address_more', 'hood_id', 'office_about', 'office_logo_url',
       'square_meters', 'hometypeid_text', 'neighborhood',
       'assetclassificationid_text', 'rooms_text', 'aboveprice', 'is_platinum',
       'is_mobile_platinum', 'processing_date']


def _get_retry_json(p):
    res = None
    for _ in range(TRIES):
        try:
            res = requests.get(url_forsale_apartments_houses.format(p))
            if res.status_code == 200:
                break
            else:
                print(f"Status code err, retry {_}/{TRIES}")
                print(res)
                time.sleep(10)
        except Exception as e:
            print(f"Caught an exception in get retry {_}/{TRIES}")
            time.sleep(10)
    if res:
        return res.json()
    return res


def insert_today_temp(df, con):
    for col, dtype in df.dtypes.items():
        if dtype == 'object':
            df[col] = df[col].astype(str)
    df.to_sql(name='yad2_today_temp', con=con, if_exists='append', index=False)


def update_today(con):
    con.execute("DROP table if exists yad2_today")
    con.execute("CREATE TABLE yad2_today AS TABLE yad2_today_temp")
    con.execute("DROP table if exists yad2_today_temp")


def _preprocess(df, today_str):
    df = df[df['type'] == 'ad'].copy()
    df['processing_date'] = today_str
    process_price = lambda x: None if x == 'לא צוין מחיר' else x.replace(',', '').replace(' ₪', '').replace(' $', '')
    # TODO: Process rooms, חדר אחד , too, info text, cordinates, etc.. according to requirement, but not critical.
    df['price'] = df['price'].apply(process_price).astype(float)
    # df = df.drop(columns=redundant_cols)
    df.columns = [c.lower() for c in df.columns]
    df = df[today_cols]
    return df


def create_tables(con):
    con.execute("DROP table if exists yad2_today_temp")
    con.execute(
        "CREATE TABLE IF NOT EXISTS yad2_forsale_history(id VARCHAR(255) not null, price float, processing_date DATE not null)")


def scraper_yad2(con):
    create_tables(con)
    res = _get_retry_json(1)
    last_page = res['data']['pagination']['last_page']
    today_dt = datetime.today()
    df = None
    for p in tqdm(range(1, last_page + 1)):
        data = _get_retry_json(p)
        data = data.get('data')
        if data is None:
            print(f"CAUTION - Could not fetch data for part {p}")
        df = pd.DataFrame.from_dict(data['feed']['feed_items'])
        df = _preprocess(df, today_dt)
        log_history(df, con)
        insert_today_temp(df, con)
    if df is not None:
        update_today(con)


def _check_exists(today_str, con):
    cnt_today = pd.read_sql(f"SELECT count(*) from yad2_forsale_history where processing_date = '{today_str}'", con).squeeze()
    if cnt_today > 0:
        raise ValueError(f"Data from {today_str} already saved in db, total {cnt_today} rows")


def log_history(df, con):
    # will dump only if a price of an id has changed from its current logged price, to save space and efficiency
    minimum_cols = ['id', 'price', 'date', 'date_added', 'processing_date']
    df = df[minimum_cols].copy()
    id_str = ','.join([f"'{x}'" for x in df['id'].to_list()])
    df_found_ids = pd.read_sql(
        f"SELECT id, price as last_price from (select id, price, processing_date, ROW_NUMBER() over (partition by id order by processing_date desc)"
        f" as rn from yad2_forsale_history where id in ({id_str})) a where rn=1", con)
    merged = df[['id', 'price']].merge(df_found_ids, left_on='id', right_on='id', how='left')
    ids_not_changed = merged[merged['price'] == merged['last_price'].astype(float)]['id'].to_list()
    df = df[~df['id'].isin(ids_not_changed)]
    df.to_sql(name='yad2_forsale_history', con=con, if_exists='append', index=False, dtype= history_dtype)


def daily_logic():
    try:
        con = sqlite3.connect('yad2.db')
        scraper_yad2(con)
        print(f"FINIHSED!")
    except Exception as e:
        print("Caught an exception at scraper yad2!", e)


if __name__ == '__main__':
    daily_logic()
    # check_exists()
    schedule.every().day.at("00:00").do(daily_logic)

    while True:
        schedule.run_pending()
        time.sleep(1)
