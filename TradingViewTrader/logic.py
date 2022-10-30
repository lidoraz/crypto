import json

from TradingViewTrader.trader import Exchange


def logic(order):
    # order = json.loads(res)
    print('*' * 60)
    print('GOT ORDER::', order)
    timeout = order['timeout']
    symbol = order['ticker'].upper()
    action = order['action']
    comment = order['comment']
    orderID = order['orderID']
    price = order['price']

    # TODO: Temp fix:
    if orderID not in ["LONG", "SHORT"]:
        # currently only support sell and buy without as TW does not allow to do close SELL options.
        return -1
    ex = Exchange(prod=True)
    curr_side, contracts = ex.has_position(symbol)
    # close positions if needed.
    if curr_side is not None:  # cant close if the order is on the same side
        print(f'current in position: {curr_side}, Attempting to close...')
        # curr_side long/short
        opp_current_side = 'sell' if curr_side == 'long' else 'sell'
        if opp_current_side == action:
            ex.exchange.create_order(symbol=symbol, type="MARKET", side=opp_current_side, amount=contracts,
                                     params={"reduceOnly": True})
            print('Closed position on', curr_side)
        else:
            print('Next order is NOT on the same opp_current_side!! ignoring')

    # Create order
    amount_udst = 40
    ex.market_order(symbol, action, amount_udst)
    with open('orders.txt', 'a') as f:
        print(order, file=f)


if __name__ == '__main__':
    res = '{"timeout": "2022-10-29T18:22:00Z", "ticker": "BTCUSDT", "action": "buy", "inteval": "1", "orderID": "SHORT", "orderContracts": "0.47966", "posSize": "0", "price": "20821.16", "comment": "SELL-LONG"}'
    logic(json.loads(res))
