import json

from TradingViewTrader.trader import Exchange


def logic(order):
    # res = '{"timeout": "2022-10-29T18:22:00Z", "ticker": "BTCUSDT", "action": "buy", "inteval": "1", "orderID": "LONG", "orderContracts": "0.47966", "posSize": "0", "price": "20821.16", "comment": "SELL-LONG"}'

    # order = json.loads(res)
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
        return
    ex = Exchange(prod=True)
    curr_side, contracts = ex.has_position(symbol)
    # close positions if needed.
    if curr_side is not None and curr_side == action:  # cant close if the order is on the same side
        # curr_side long/short
        close_side = 'sell' if curr_side == 'long' else 'buy'
        ex.exchange.create_order(symbol=symbol, type="MARKET", side=close_side, amount=contracts,
                                 params={"reduceOnly": True})
        print('Closed position on', curr_side)
    # Create order
    amount_udst = 40
    ex.market_order(symbol, action, amount_udst)


if __name__ == '__main__':
    logic(None)
