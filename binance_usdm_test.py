import ccxt  # noqa: E402
import os


class BinanceFutures:
    def __init__(self, prod):
        self.exchange = ccxt.binanceusdm({
            'apiKey': os.environ.get('BINANCE_API'),
            'secret': os.environ.get('BINANCE_SECRET'),
        })
        self.prod = prod
        self.pct_to_curr_price = 0.0010
        self.exchange_name = 'BINANCE'
        markets = self.exchange.load_markets()
        # market = self.exchange.market('BTC/USDT')
        # .private_post_order_oco({
        #                         'symbol': market['id'],
        #                         'side': 'SELL',  # SELL, BUY
        #                         'quantity': f_amount,
        #                         'price': f_win_price,
        #                         'stopPrice': f_stop_price,
        #                         'stopLimitPrice': f_lose_price,  # If provided, stopLimitTimeInForce is required
        #                         'stopLimitTimeInForce': 'GTC',  # GTC, FOK, IOC
        #                     })
        # exchange.verbose = True  # uncomment for debugging purposes
        #  exchange.fetch_open_orders(symbol)
        #  exchange.cancel_all_orders(symbol)

    def remove_unlocked_positions(self, symbols):
        symbols = [f'{symbol}/USDT' for symbol in symbols]
        try:
            symbols_with_positions = self._get_all_positions(symbols)
            for symbol in symbols:
                if not symbols_with_positions:
                    if len(self.exchange.fetch_open_orders(symbol)) > 0:
                        self.exchange.cancel_all_orders(symbol)
                        print(f'Canceled open order for closed position in {symbol}')
        except Exception as e:
            print(type(e).__name__, str(e))
            return -1

    def _get_all_positions(self, symbols):
        res = [res['symbol'] for res in self.exchange.fetchPositions() if
               res['symbol'] in symbols and res['contracts'] > 0.0]
        return res

    def has_position(self, symbol):
        res = [res for res in self.exchange.fetchPositions() if res['symbol'] == symbol][0]
        # print(res)
        return res['contracts'] > 0.0

    def create_order(self, symbol, amount, side, stop_loss_price, take_profit_price):
        if self.has_position(symbol):
            print(f'{symbol} Has active position...')
            return -2
        code = self._create_order(symbol, side, amount, stop_loss_price, take_profit_price)
        return code

    def _create_order(self, symbol, amount_req, side, stop_loss, take_profit):
        assert side in ('buy', 'sell')
        amount = self.exchange.amount_to_precision(symbol, amount_req)
        print(amount_req, amount)
        if not self.prod:
            print('called create_order, but (prod = False), returning')
            return
        # rw: 1:1 -> 1, 1:2 -> 2
        try:
            print(f'-> Order Request {symbol}, {side}, {amount}, ({stop_loss}, {take_profit})')
            print(f'AMOUNTS: Req vs pre_amount:, {amount_req} -> {amount}')
            # TODO: Check what if {'reduceOnly': True} in params
            #  Check hard-limit of 50orders per 10sec : https://www.binance.com/en/support/faq/360004492232
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
                                                       {'stopPrice': stop_loss,
                                                        "reduceOnly": True})
            print(stopLossOrder)
            # print(symbol, 'STOP_MARKET', inverted_side, amount, price, stopLossParams)
            takeProfitOrder = self.exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', inverted_side, amount, None,
                                                         {'stopPrice': take_profit,
                                                          "reduceOnly": True})
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

    trader = BinanceFutures(False)

    if not trader.has_position(symbol):
        trader._create_order(symbol, side, amount, stop_price, rw_ratio)
    else:
        print('Has active position...')


if __name__ == '__main__':
    check_trading()
