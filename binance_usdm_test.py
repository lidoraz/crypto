import ccxt  # noqa: E402
import os


class BinanceFutures:
    def __init__(self, prod):
        self.exchange = ccxt.binanceusdm({
            'apiKey': os.environ.get('BINANCE_API'),
            'secret': os.environ.get('BINANCE_SECRET'),
        })
        self.pct_to_curr_price = 0.0010
        self.exchange_name = 'BINANCE'
        self.prod = prod
        markets = self.exchange.load_markets()
        # exchange.verbose = True  # uncomment for debugging purposes
        #  exchange.fetch_open_orders(symbol)
        #  exchange.cancel_all_orders(symbol)

    def has_position(self, symbol):
        res = [res for res in self.exchange.fetchPositions() if res['symbol'] == symbol][0]
        # print(res)
        return res['contracts'] > 0.0

    def create_order(self, symbol, amount, side, stop_loss_price, take_profit_price):
        if not self.has_position(symbol):
            code = self._create_order(symbol, amount, side, stop_loss_price, take_profit_price)
            return code
        else:
            print(f'{symbol} Has active position...')
            return -2

    def _create_order(self, symbol, amount, side, stop_loss, take_profit):
        assert side in ('buy', 'sell')
        if not self.prod:
            print('called create_order, but (prod = False), returning')
            return
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
            inverted_side = 'sell' if side == 'buy' else 'buy'
            stop_loss = self.exchange.price_to_precision(symbol, stop_loss)
            take_profit = self.exchange.price_to_precision(symbol, take_profit)
            stopLossOrder = self.exchange.create_order(symbol, 'STOP_MARKET', inverted_side, amount, None,
                                                       {'stopPrice': stop_loss})
            print(stopLossOrder)
            # print(symbol, 'STOP_MARKET', inverted_side, amount, price, stopLossParams)
            takeProfitOrder = self.exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', inverted_side, amount, None,
                                                         {'stopPrice': take_profit})
            print(takeProfitOrder)
            print('##--CREATED_ORDER--->', symbol, side, price_exec, stop_loss, take_profit)
            return 0

        except Exception as e:
            print(type(e).__name__, str(e))
            return -1


def check_trading():
    # must check that stopPrice > price if sell, and stopPrice < price if buy.
    # usdt_amount / curr_price
    symbol = 'BTC/USDT'
    side = 'sell'  # 'sell'
    amount = 0.001  # amount in bitcoin.
    stop_price = 21000 if side == 'sell' else 19000
    rw_ratio = 1
    # TODO: Close position ->
    # close_position = binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=pos['positionAmt'], params={"reduceOnly": True})
    # TODO: MUST TEST THAT STOPPRICE IS CORRECT CURR PRICE AND SIDE!!
    # Margin is set related to the symbol in the app, also can be set in the api, but not really needed.

    trader = BinanceFutures(True)

    if not trader.has_position(symbol):
        trader._create_order(symbol, amount, side, stop_price, rw_ratio)
    else:
        print('Has active position...')


if __name__ == '__main__':
    check_trading()
