def get_asset_holding_amount(exchange, coin=None):
    balances = exchange.fetch_balance()
    assets = [d for d in balances['info']['balances'] if float(d['free']) > 0]
    if coin:
        return [float(v['free']) for v in assets if v['asset'] == coin][0]
    else:
        return dict([(v['asset'], float(v['free'])) for v in assets])


def get_split_buy_amount(order_usdt_value, buy_price):
    amount = order_usdt_value / buy_price
    return amount


def get_current_price(exchange, symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']
