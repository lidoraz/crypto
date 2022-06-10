from Analytics.binance_fetch_all_trades import get_table
from Analytics.dash_utils import calc_trade_pct


def anaylize_trades():
    raw_trades = get_table()
    df = calc_trade_pct(raw_trades)
    dff = df[df['buy_dt'] > '2022-05-27']
    dff.groupby('symbol')['sell_buy_price'].sum().sort_values(ascending=False)
    # filter by 27 May, then group and sum by symbol over ROI, get best.



if __name__ == '__main__':
    anaylize_trades()