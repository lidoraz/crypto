from Strategy.DataWrap import CryptoData
from Strategy.Strategies import BB, RSIBB
from Utils.utils import WaitToMinEveryHour
from RealtimeCommandsBroadcast import get_latest_buy_sell
from datetime import datetime
from Utils.notify import TelegramBot
import pandas as pd
from dateutil import tz
import ccxt

prod = False


def handle_buy_sell(buy_lst, sell_lst, exchange):
    TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime

    if len(buy_lst):
        print(buy_lst)
    if len(sell_lst):
        print(sell_lst)


def handle_args():
    import sys
    args = sys.argv[1:]
    usage = 'usage: 15min or 1h'
    if len(args) == 1:
        if args[0].lower() == '15min':
            trigger_minutes = [0, 15, 30, 45]
            return '15min', trigger_minutes
        if args[0].lower() == '1h':
            trigger_minutes = [0]
            return '1h', trigger_minutes
    print(usage)
    exit(-1)


# Test validity of this algorithm, and how to use it.
# looks on the bright side that the async code works well and did not crash during weekend.
if __name__ == '__main__':
    import os

    exchange = ccxt.binance({
        # 'apiKey': os.environ.get('BINANCE_API'),
        # 'secret': os.environ.get('BINANCE_SECRET'),
        'enableRateLimit': True,
    })


    def get_current_price(exchange, symbol):
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']


    print('buy value', get_current_price(exchange, 'BTC/USDT'))

    print('Use with CAUTION!')
    exit(-1)

    print(exchange.requiredCredentials)  # prints required credentials
    exchange.checkRequiredCredentials()  # raises AuthenticationError
    import json


    def get_asset_holding_amount(exchange, coin=None):
        balances = exchange.fetch_balance()
        assets = [d for d in balances['info']['balances'] if float(d['free']) > 0]
        if coin:
            return [v['free'] for v in assets if v['asset'] == coin][0]
        else:
            return [(v['asset'], v['free']) for v in assets]


    print(get_asset_holding_amount(exchange))


    #
    # # exchange.create_order(symbol, type, side, amount, price = undefined, params = {})
    # TODO: Minimum binance value for order = 10 usd

    def get_split_buy_amount(order_usdt_value, buy_price):
        amount = order_usdt_value / buy_price
        return amount


    order_usdt_value = 10
    buy_price = 10000
    amount = get_split_buy_amount(order_usdt_value, buy_price)
    symbol = 'BTC/USDT'
    #  params={'test': True}

    # https://www.investopedia.com/articles/active-trading/091813/which-order-use-stoploss-or-stoplimit-orders.asp
    # I think for this kind of trades, its best to use limit with buy / sell, or even go straight with market order.
    # The orders are created online every our, so there is no worry to sell /buy when we get the exact price.
    #    exchange.create_order(symbol, 'market', side, amount, ...)
    # TODO: MARKET will buy at market price!!!
    # TODO: Buy command at limit price.
    # WORKS -> Limit/Buy Amount - 0/0.0001, Price 10,000
    # order = exchange.create_order(symbol, 'limit', 'buy', amount, price=buy_price,)
    # print(order)
  
    # TODO: Sell command at limit price.
    # WORKS -> Limit/Sell Amount - 0/0.0001, Price 100,000
    # order = exchange.create_order(symbol, 'limit', 'sell', amount, price=100000)
    ##############################################################################################################
    # print(order)

    # WORKS:
    # TODO: When there is an open an order to sell, the quantity will be 0 as the asset is not free anymore.
    #  This means that if we want do algo sell, we must cancel the stop loss.
    # TODO: StopLoss Lose
    # WORKS -> Stop Limit / Sell Price: 22,999 Conition <= 23000
    # order = exchange.create_order('BTC/USDT', 'STOP_LOSS_LIMIT', 'sell', amount, price=22999, params={'stopPrice': 23000})
    # TODO: StopLoss Win (Take profit)
    # WORKS  -> Stop Limit / Sell, Price: 36,000, Condition >= 35000
    # order = exchange.create_order('BTC/USDT', 'TAKE_PROFIT_LIMIT', 'sell', amount, price=36000,
    #                               params={'stopPrice': 35000})
    # TODO have more combinations with buy buy i dont see the need of it, only need buy.
    # order = exchange.create_order('BTC/USDT', 'TAKE_PROFIT_LIMIT', 'buy', amount, price=35000,
    #                               params={'stopPrice': 36000})
    # cancel an order given an id, must provide a symbol
    ## IMPORTANT KEYS:
    # order['id'], order['symbol'] ## id = '10573785159', 'symbol' = 'BTCUSDT' 'fee'
    # exchange.cancel_order('10573785159', 'BTCUSDT')
    # print(order)

    print()
    # STOP_LOSS_LIMIT
    ########################################################################################################################

    # # sell order
    # btc_amount = get_asset_holding_amount(assets, 'BTC')
    # amount = btc_amount
    # order = exchange.create_order('BTC/USDT', 'limit', 'sell', amount, price=40000)
    # print(order)
    # stopLimit
    # exchange.cancel_order()
    # exchange.create_order()
    # exchange.create_limit_buy_order()
    # exchange.create_limit_sell_order()
    # exchange.create_stop_limit_order()
    exit(0)

    timeframe, trigger_minutes = handle_args()
    print(f'Broadcasting every {timeframe}, at {trigger_minutes} min every hour')

    data_wrapper = CryptoData.get_wrapper(live=True, start_date='2022-05-01')
    symbols = data_wrapper.get_symbols()
    strategy = BB()
    # strategy = RSIBB(dict(RSIBB_n_rsi_soon=5, RSIBB_ind_ahead=14, RSIBB_BB_std=2.5))

    tb_notify = TelegramBot()
    buy_change = set()
    sell_change = set()
    owned_coins = set()
    wait = WaitToMinEveryHour(trigger_minutes)
    title_strategy = f'{strategy}({timeframe})'
    str_symbols = ", ".join(symbols)
    start_msg = f'{title_strategy}\nFollowing: {str_symbols}'
    print(start_msg)
    # if prod:
    #     tb_notify.send(start_msg)

    while True:
        if prod:
            wait.wait()
        time_now_minus_tf = datetime.now(tz.gettz('Israel')) - pd.to_timedelta(timeframe)
        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, time_now_minus_tf, symbols, strategy,
                                                                tf=timeframe)

        buy_curr = set([detail['coin'] for detail in buy_details_lst])
        notify_coins = buy_curr - buy_change
        buy_change = buy_curr
        buy_notify = [detail for detail in buy_details_lst if detail['coin'] in notify_coins]

        sell_curr = set([detail['coin'] for detail in sell_details_lst])
        notify_coins = sell_curr - sell_change
        sell_change = sell_curr
        sell_notify = [detail for detail in sell_details_lst if detail['coin'] in notify_coins]

        owned_coins.add(buy_notify)
        sell_notify = [c for c in sell_notify if c in owned_coins]
        print('-> Getting time_now_minus_tf =', time_now_minus_tf)
        print('buy_lst', buy_details_lst)
        # print('buy_change:', buy_change)
        print('buy_notify:', buy_notify)
        print('sell_lst', sell_details_lst)
        # print('sell_change:', sell_change)
        print('sell_notify:', sell_notify)
        handle_buy_sell(title_strategy, buy_notify, sell_notify, tb_notify)
