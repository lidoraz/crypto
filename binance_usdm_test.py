import ccxt  # noqa: E402
import os


class BinanceFutures:
    def __init__(self):
        self.exchange = ccxt.binanceusdm({
            'apiKey': os.environ.get('BINANCE_API'),
            'secret': os.environ.get('BINANCE_SECRET'),
        })
        self.pct_to_curr_price = 0.0010
        markets = self.exchange.load_markets()
        # exchange.verbose = True  # uncomment for debugging purposes
        #  exchange.fetch_open_orders(symbol)
        #  exchange.cancel_all_orders(symbol)

    def has_position(self, symbol):
        res = [res for res in self.exchange.fetchPositions() if res['symbol'] == symbol][0]
        print(res)
        return res['contractSize'] > 0.0

    def create_order(self, symbol, amount, side, stop_price, rw_ratio=1):
        assert side in ('buy', 'sell')
        # rw: 1:1 -> 1, 1:2 -> 2
        amount = self.exchange.amount_to_precision(symbol, amount)
        try:
            self.exchange.cancel_all_orders(symbol)  # Release any funds in order.
            order = self.exchange.create_order(symbol, 'MARKET', side, amount)
            # order = {'price': 20000, 'amount': 0.001}
            print(order)
            price_exec = order['price']
            # check if this equals to real amount. acutally if we sell or buy btc amount it does not matter.
            amount_ = order['amount']
            inverted_side = 'sell'
            price_to_stop = abs(price_exec - stop_price)
            if side == 'buy':  # long
                stopLossPrice = stop_price
                takeProfitPrice = price_exec + rw_ratio * price_to_stop
                if price_exec / stop_price < 1 - self.pct_to_curr_price:
                    print(f'stop price too close to exec_price: less than {self.pct_to_curr_price}')
            else:  # short
                stopLossPrice = stop_price
                takeProfitPrice = price_exec - rw_ratio * price_to_stop
                if price_exec / stop_price < 1 + self.pct_to_curr_price:
                    print(f'stop price too close to exec_price: less than {self.pct_to_curr_price}')
            stopLossPrice = self.exchange.price_to_precision(symbol, stopLossPrice)
            takeProfitPrice = self.exchange.price_to_precision(symbol, takeProfitPrice)

            print(symbol, side, price_exec, stopLossPrice, takeProfitPrice)
            stopLossOrder = self.exchange.create_order(symbol, 'STOP_MARKET', inverted_side, amount, None,
                                                       {'stopPrice': stopLossPrice})
            print(stopLossOrder)
            # print(symbol, 'STOP_MARKET', inverted_side, amount, price, stopLossParams)
            takeProfitOrder = self.exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', inverted_side, amount, None,
                                                         {'stopPrice': takeProfitPrice})
            print(takeProfitOrder)
            # print(symbol, 'TAKE_PROFIT_MARKET', inverted_side, amount, price,
            #       takeProfitParams)

        except Exception as e:
            print(type(e).__name__, str(e))


def check_trading():
    # must check that stopPrice > price if sell, and stopPrice < price if buy.
    # usdt_amount / curr_price
    symbol = 'BTC/USDT'
    side = 'buy'  # 'sell'
    amount = 0.001  # amount in bitcoin.
    stop_price = 21000 if side == 'sell' else 19000
    rw_ratio = 1
    # TODO: MUST TEST THAT STOPPRICE IS CORRECT CURR PRICE AND SIDE!!
    # Margin is set related to the symbol in the app, also can be set in the api, but not really needed.

    trader = BinanceFutures()

    if not trader.has_position(symbol):
        trader.create_order(symbol, amount, side, stop_price, rw_ratio)
    else:
        print('Has active position...')

if __name__ == '__main__':
    check_trading()
