import ccxt  # noqa: E402
import os


class Exchange:
    def __init__(self, prod) -> None:
        assert os.environ.get('BINANCE_API') and os.environ.get('BINANCE_SECRET')
        self.exchange = ccxt.binanceusdm({
            'apiKey': os.environ.get('BINANCE_API'),
            'secret': os.environ.get('BINANCE_SECRET'),
            'options': {
                'adjustForTimeDifference': True,
            },
        })
        # self.exchange.set_sandbox_mode(True)
        self.prod = prod
        # self.pct_to_curr_price = 0.0010
        # self.exchange_name = 'BINANCE'
        markets = self.exchange.load_markets()

    # def get_asset_holding_amount(self, coin):
    #     # todo: generalize this withoutt using info
    #     balances = self.exchange.fetch_balance()
    #     balances = balances['info']['assets']
    #     coin_balances = [d for d in balances if float(d['free']) > 0 or float(d['locked']) > 0]
    #     free_coin_tup = [(float(v['free']), float(v['locked'])) for v in coin_balances if v['asset'] == coin]
    #     if len(free_coin_tup):
    #         balance_free, balance_locked = free_coin_tup[0]
    #         return balance_free, balance_locked
    #     else:
    #         return 0, 0

    def get_all_positions(self, symbols):
        positions = self.exchange.fetchPositions()
        res = [res['symbol'] for res in positions if
               res['symbol'] in symbols and res['contracts'] > 0.0]
        return res

    def has_position(self, symbol):
        if '/' not in symbol:
            symbol = f'{symbol[: -4]}/{symbol[-4:]}'
        res = next(filter(lambda x: x['symbol'] == symbol, self.exchange.fetchPositions()))
        print('has_position', res)
        if res['contracts']:
            return res['side'], res['contracts']
        else:
            return None, None

    def market_order(self, symbol, side, usdt_amount):
        assert side in ('buy', 'sell')
        curr_price = self.exchange.fetchTicker(symbol)['last']
        amount = usdt_amount / curr_price

        amount_p = self.exchange.amount_to_precision(symbol, amount)
        print(amount_p, amount)
        if not self.prod:
            print('called create_order, but (prod = False), returning')
            return
        print(f'-> Order Request {symbol}, {side}, {amount}')
        print(f'AMOUNTS: Req vs pre_amount:, {amount_p} -> {amount}')
        res = self.exchange.create_order(symbol, "MARKET", side, amount_p)
        print('--> Filled MARKET order', res)


if __name__ == '__main__':
    ex = Exchange(prod=True)
#
# print(ex.exchange.positions)
# symbols = ['BTCUSDT', 'ETHUSDT', 'SUSHIUSDT', 'DOGEUSDT']
# print(ex.get_all_positions(symbols))
# # print(ex.get_asset_holding_amount('USDT'))
# print(ex)


# ex.market_order("BTCUSDT", "SELL", 50)
# side, contracts = ex.has_position("BTC/USDT")
