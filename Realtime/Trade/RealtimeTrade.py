from Realtime.Trade.mocks import *
from Realtime.Trade.persistence_trades_simple import PersistenceOrders
import ccxt
import os
import time


def fix_order_type(res):
    if res['type'] is None:
        res['type'] = 'CANCEL_ALL_ORDERS'


def parse_oco_response(response):
    """
    Parses Binance OCO response for RealtimeTrade
    :param response:
    :return:
    """
    reports = response['orderReports']
    if len(reports) != 2:
        raise ValueError('Bad request, should be exact 2 responses')
    if reports[0]['type'] == 'STOP_LOSS_LIMIT':  # thats a stoploss limit:
        lose_idx = 0
    else:
        lose_idx = 1
    order = reports[lose_idx]
    symbol_lose = order['symbol']

    def _parse(res):
        return dict(id=int(res['orderId']), timestamp=int(res['transactTime']), price=float(res['price']),
                    amount=float(res['origQty']), stopPrice=float(res.get('stopPrice', 0)), side=res['side'],
                    type=res['type'], timeInForce=res['timeInForce'], status=res['status'],
                    datetime=None, remaining=0, filled=0)

    details_stop_lose = _parse(order)
    res = reports[1 - lose_idx]
    symbol_win = order['symbol']
    details_stop_win = _parse(res)
    assert symbol_lose == symbol_win
    orders_details = [details_stop_lose, details_stop_win]
    return orders_details


# TODO: ADD check if symbol is active, along with refresh to the markets.
# TODO: Currently only supports Binance as OCO is a tricky command
class RealtimeTrade:
    """
    # Codes: 0 success / buy , sell
    #        -1 failed buy / sell
    #        -2 failed to set stop loss, buy worked
    #        -3 not enough funds. Buy / Sell
    """

    def _check_init(self):
        if self.stable_coin_min_amount > self.stable_coin_trade_amount or self.stable_coin_min_amount < 10:
            raise ValueError('stable_coin values not valid')
        if os.environ.get('BINANCE_API') is None or os.environ.get('BINANCE_SECRET') is None:
            raise EnvironmentError('API / Secret not set')

    def __init__(self, prod):
        self.db = PersistenceOrders('trade_orders.db')
        self.is_production = prod
        self.stable_coin_name = 'USDT'
        self.stable_coin_trade_amount = 12
        self.stable_coin_min_amount = 10
        self.price_diff_pct = 0.05
        self.sell_price_from_stop_pct = 0.99
        self._check_init()
        exchange = ccxt.binance({
            'apiKey': os.environ.get('BINANCE_API'),
            'secret': os.environ.get('BINANCE_SECRET'),
            'enableRateLimit': True,
        })
        self.exchange_name = 'BINANCE'
        self.exchange = exchange
        self.refresh_markets()
        print(f'Init exchange: {self.exchange_name}\n'
              f'Each Buy:-> {self.stable_coin_trade_amount} {self.stable_coin_name} in value\n'
              f'Each Sell:-> Unlimited, minimum {self.stable_coin_min_amount} {self.stable_coin_name} in value')

    def refresh_markets(self):
        # need to be loaded periodically !!
        # This is done in ccxt every create / cancel/ order
        try:
            self.exchange.load_markets()
        except Exception as e:
            print(self.exchange_name, f'load_markets failed:', type(e).__name__, str(e))

    def get_assets_holding(self, convert_to_usd=True, filter_out_val=10):
        # filter out by 10 USD value.
        try:
            balances = self.exchange.fetch_balance()
            balances = {k: balances[k] for k in balances if k in self.exchange.currencies}
            coin_balances = {k: balances[k]['total'] for k in balances}
            coin_balances = {k: v for k, v in coin_balances.items() if v > 0}
            coin_balances_sorted = {k: v for k, v in
                                    sorted(coin_balances.items(), key=lambda item: item[1], reverse=True)}

            if convert_to_usd:
                owned_assets_beside_stable = [f'{c}/{self.stable_coin_name}' for c in coin_balances]
                tickers_owned = self.exchange.fetch_tickers(
                    owned_assets_beside_stable)  # fetches all tickers, a bit expensive
                coins_owned_last = {ticker.split('/')[0]: tickers_owned[ticker]['last'] for ticker in tickers_owned}
                coin_balances_usd = {k: v * coins_owned_last[k] for k, v in coin_balances.items() if
                                     k in coins_owned_last}
                coin_balances_usd[self.stable_coin_name] = coin_balances[self.stable_coin_name]  # insert stable coin
                coin_balances_usd = {k: v for k, v in
                                     sorted(coin_balances_usd.items(), key=lambda item: item[1], reverse=True)}
                coin_balances_usd = {k: v for k, v in coin_balances_usd.items() if v > filter_out_val}
                return coin_balances_usd
            return coin_balances_sorted
        except Exception as e:
            print(self.exchange_name, f'get_assets_holding failed:', type(e).__name__, str(e))
            raise e

    def _get_current_price(self, symbol):
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']

    def _get_asset_holding_amount(self, coin):
        # todo: generalize this withoutt using info
        balances = self.exchange.fetch_balance()
        coin_balances = [d for d in balances['info']['balances'] if float(d['free']) > 0 or float(d['locked']) > 0]
        free_coin_tup = [(float(v['free']), float(v['locked'])) for v in coin_balances if v['asset'] == coin]
        if len(free_coin_tup):
            balance_free, balance_locked = free_coin_tup[0]
            return balance_free, balance_locked
        else:
            return 0, 0

    def _add_order_to_db(self, symbol, res):
        # order_timestamp = int(order_details.get(['timestamp'], 0)) // 1000
        timestamp = int(time.time())
        try:
            trade_id = int(res['id'])
        except TypeError:
            trade_id = -1
        valuation = res.get('valuation', 0)
        order_dt = res.get('datetime', None)
        res = dict(ts=timestamp, id=trade_id, symbol=symbol, type=res['type'], side=res['side'],
                   price=res['price'], amount_req=res['amount'], amount_filled=res['filled'],
                   valuation=valuation, stopPrice=res['stopPrice'],
                   status=res['status'], order_dt=order_dt, exchange=self.exchange_name)
        print(f'Adding to DB:\n {res}')
        if self.is_production:
            # with open('order_history.txt', 'a') as fp:
            #     print(res, file=fp)
            self.db.add_order(res)

    def _check_buy_and_price(self, coin):
        use_locked = False
        symbol = f'{coin}/{self.stable_coin_name}'
        amount_holding, amount_locked = self._get_asset_holding_amount(self.stable_coin_name)
        curr_price = self._get_current_price(symbol)
        is_enough_funds = amount_holding > self.stable_coin_trade_amount
        # # check if locked is needed, as the usdt will never be on an open order.
        # is_enough_locked_funds = amount_locked * curr_price > self.stable_coin_trade_amount
        # if not is_enough_funds and is_enough_locked_funds:  # try with locked
        #     is_enough_funds = True
        #     use_locked = True
        if not is_enough_funds:
            raise ccxt.errors.InsufficientFunds(
                f'Not enough {self.stable_coin_name} to buy {coin} at: (curr_price={curr_price}, amount_stable={self.stable_coin_trade_amount}, use_locked={use_locked})')
        return curr_price, use_locked

    def _create_market_buy(self, coin, buy_price, stop_loss_price, stop_win_price):
        symbol = f'{coin}/{self.stable_coin_name}'
        try:
            self._check_algo_price(symbol, buy_price)
            curr_price, use_locked = self._check_buy_and_price(coin)
            amount = self.stable_coin_trade_amount / curr_price
            f_curr_price = self.exchange.price_to_precision(symbol, curr_price)
            f_amount = self.exchange.amount_to_precision(symbol, amount)
            print(f'Market Buy: {symbol} - price(ticker)={f_curr_price}, amount={f_amount},'
                  f' value={self.stable_coin_trade_amount} {self.stable_coin_name}($)')
            if self.is_production:
                order_details = self.exchange.create_order(symbol, 'MARKET', 'BUY',
                                                           amount=f_amount)  # price=f_curr_price
            else:
                order_details = mock_binance_market_buy()
            order_details['valuation'] = self.stable_coin_trade_amount
            self._add_order_to_db(symbol, order_details)
            time.sleep(5)  # sleep few seconds to allow register #
            code = self._create_binance_sell_oco_order(coin, stop_loss_price, stop_win_price, order_details['filled'],
                                                       retry=True)
            # self._create_stop_loss_request(coin, stop_loss_price, order_details)
            return code
        except Exception as e:
            print(self.exchange_name, symbol, f'failed create MARKET-BUY order:', type(e).__name__, str(e))
            if isinstance(e, ccxt.errors.InsufficientFunds):
                return -3
            return -1

    # Buy at 10usdt each, sell everything......
    def _check_sell_and_price(self, coin):
        """
        TODO: There it will prefer to take free amount instead of using both free and locked, thing if this is the right way.
            ADD option when there were multiple buys, to cancel all of them when trying to sell! this will free up everything.
            # solution: Can combine amount + amount locked, to one, and test if needs to be unlocked to release the locked funds, do that.
        :param coin:
        :return:
        """
        use_locked = False
        symbol = f'{coin}/{self.stable_coin_name}'
        amount, amount_locked = self._get_asset_holding_amount(coin)
        curr_price = self._get_current_price(symbol)
        amount_stable = amount * curr_price  # convert to stable coin
        is_enough_funds = amount_stable > self.stable_coin_min_amount
        amount_locked_stable = amount_locked * curr_price
        if amount_locked_stable > self.stable_coin_min_amount:  # try with locked, combine
            amount = amount_locked + amount
            amount_stable = amount_locked_stable + amount_stable
            is_enough_funds = True
            use_locked = True
        if not is_enough_funds:
            raise ccxt.errors.InsufficientFunds(f'Not enough {coin} to sell (curr_price={curr_price}, '
                                                f'amount={amount}, amount_stable={amount_stable}, use_locked={use_locked})')
        return curr_price, amount, amount_stable, use_locked

    def _check_algo_price(self, symbol, req_price):
        curr_price = self._get_current_price(symbol)
        diff_pct = (req_price / curr_price) - 1
        if diff_pct > self.price_diff_pct:  # 0.09 > 0.05
            print(f'Warning: {symbol} algo price *LARGER* than {int(self.price_diff_pct * 100)}%'
                  f' (sell_price={req_price}, curr_price={curr_price}, diff={diff_pct:.2%})')
        elif diff_pct < -self.price_diff_pct:  # -0.09 < -0.05
            print(f'Warning: {symbol} algo price **LOWER** than {int(self.price_diff_pct * 100)}%'
                  f' (sell_price={req_price}, curr_price={curr_price}, diff={diff_pct:.2%})')

    def _unlock_symbol(self, symbol):

        # self.exchange.fetch_open_orders(symbol)
        if self.is_production:
            order_details = self.exchange.cancel_all_orders(symbol)
        else:
            order_details = mock_binance_cancel_stop_loss()
        print('Canceled all orders for:', symbol)
        if isinstance(order_details, list):
            if len(order_details) > 1:
                print(f'Warning: Canceled more than {len(order_details)} order for {symbol}')
            for order_details in order_details:
                if not order_details['type']:
                    fix_order_type(order_details)
                self._add_order_to_db(symbol, order_details)
        else:
            fix_order_type(order_details)
            self._add_order_to_db(symbol, order_details)

    def _create_market_sell(self, coin, sell_price):
        """
        # BEFORE WE ARE ABLE TO SELL, need to cancel stoploss request, and check there is enough amount.
        # Will attempt to sell all amount of holding from coin
        :param coin:
        :param sell_price:
        :return:
        """
        symbol = f'{coin}/{self.stable_coin_name}'
        try:
            self._check_algo_price(symbol, sell_price)
            curr_price, amount_holding, amount_stable, use_locked = self._check_sell_and_price(coin)
            if use_locked:
                self._unlock_symbol(symbol)
            f_amount = self.exchange.amount_to_precision(symbol, amount_holding)
            f_sell_price = self.exchange.price_to_precision(symbol, curr_price)
            print(f'Market Sell: {symbol} - price(curr)={f_sell_price}, amount={f_amount},'
                  f' trade_value={amount_stable:.5} {self.stable_coin_name}($)')
            if self.is_production:
                order_details = self.exchange.create_order(symbol, 'MARKET', 'SELL', amount=f_amount)
            else:
                order_details = mock_binance_market_sell()
            order_details['valuation'] = amount_stable
            self._add_order_to_db(symbol, order_details)
            return 0
        except Exception as e:
            print(self.exchange_name, symbol, f'failed create MARKET-SELL order:', type(e).__name__, str(e))
            if isinstance(e, ccxt.errors.InsufficientFunds):
                return -3
            return -1

    def _create_binance_sell_oco_order(self, coin, stop_price, win_price, amount_filled, retry):
        # create sell oco order (what comes first)
        # | stop_price_lose <- stop_price  <-(-)-curr_price-(+)->  price_win |
        symbol = f'{coin}/{self.stable_coin_name}'
        ex = self.exchange
        # TODO: #Add an option to try few times if it fails after buy request (let it register)
        f_amount, f_win_price, f_stop_price, f_lose_price, e = (None, None, None, None, None)
        max_tries = 5 if retry else 1
        n_tries = 0
        while n_tries < max_tries:
            try:
                market = ex.market(symbol)  # market should be loaded, if not will throw error
                f_amount = ex.amount_to_precision(symbol, amount_filled)
                f_win_price = ex.price_to_precision(symbol, win_price)
                f_stop_price = ex.price_to_precision(symbol, stop_price)
                f_lose_price = ex.price_to_precision(symbol, stop_price * self.sell_price_from_stop_pct)
                if self.is_production:
                    response = ex.private_post_order_oco({
                        'symbol': market['id'],
                        'side': 'SELL',  # SELL, BUY
                        'quantity': f_amount,
                        'price': f_win_price,
                        'stopPrice': f_stop_price,
                        'stopLimitPrice': f_lose_price,  # If provided, stopLimitTimeInForce is required
                        'stopLimitTimeInForce': 'GTC',  # GTC, FOK, IOC
                    })
                else:
                    response = mock_binance_sell_oco()
                res = parse_oco_response(response)
                for order_details in res:
                    self._add_order_to_db(symbol, order_details)
                return 0
            except Exception as e:
                n_tries += 1
                print(self.exchange_name, symbol, f'failed create STOP_LOSS_SELL order ({n_tries}/{max_tries}):',
                      type(e).__name__, str(e),
                      f'(f_amount={f_amount}, f_win_price={f_win_price},'
                      f' f_stop_price={f_stop_price}, f_lose_price={f_lose_price})')
                time.sleep(3)
        print(self.exchange_name, symbol, f'Failed create STOP_LOSS_SELL order, max tries over.')
        return -2

    # Replaced for oco stop_loss
    def _create_stop_loss_request(self, coin, stop_price, order_details):
        symbol = f'{coin}/{self.stable_coin_name}'
        amount = order_details['filled']
        sell_price = stop_price * self.sell_price_from_stop_pct
        f_amount = self.exchange.amount_to_precision(symbol, amount)
        f_stop_price = self.exchange.price_to_precision(symbol, sell_price)
        f_sell_price = self.exchange.price_to_precision(symbol, sell_price)
        try:
            curr_price, amount_holding, amount_holding_stable, use_locked = self._check_sell_and_price(coin)
            if not use_locked:
                if self.is_production:
                    order_details = self.exchange.create_order(symbol, 'STOP_LOSS_LIMIT', 'sell', f_amount,
                                                               price=f_sell_price, params={'stopPrice': f_stop_price})
                else:
                    order_details = mock_binance_create_sell_stop_loss()
                self._add_order_to_db(symbol, order_details)
            else:
                raise ValueError(f'Trying to create stop_loss order when there is amount locked for {coin}')
        except Exception as e:
            print(self.exchange_name, symbol, f'failed create STOP_LOSS-SELL order:', type(e).__name__, str(e),
                  f'details: f_amount={f_amount} f_stop_price={f_stop_price}, f_sell_price{f_sell_price}')

    # Codes: 0 success / buy , sell
    #        -1 failed buy / sell
    #        -2 failed to set stop loss, buy worked
    #        -3 not enough funds. Buy / Sell
    def handle_buy(self, buy_details):
        coin = buy_details['coin']
        buy_price = buy_details['buy_price']
        stop_loss_price = buy_details['sell_price_lose_stop']
        stop_win_price = buy_details['sell_price_win_stop']
        code = self._create_market_buy(coin, buy_price, stop_loss_price, stop_win_price)
        return code  # codes above

    def handle_sell(self, sell_details):
        coin = sell_details['coin']
        sell_price = sell_details['sell_price']
        code = self._create_market_sell(coin, sell_price)
        return code  # codes above


def show_portfolio_value(trader):
    all_holding_usdt = trader.get_assets_holding()
    print(all_holding_usdt)


def test_buy_stop_sell_works(trader):
    buy_details = {'buy_idx': 0, 'buy_price': 1.168, 'sell_price_win_stop': 1.3, 'sell_price_lose_stop': 1.1,
                   'coin': 'CRV'}
    print(buy_details)
    trader.handle_buy(buy_details)
    time.sleep(5)
    sell_details = {'sell_idx': 0, 'sell_price': 1.168, 'coin': 'CRV'}
    print(sell_details)
    trader.handle_sell(sell_details)


def test_buy_stop_sell_fails(trader):
    # Fails at setting stoploss, but then sells the asset.
    # buy_details = {'buy_idx': 0, 'buy_price': 1.168, 'sell_price_win_stop': 1.28, 'sell_price_lose_stop': 1.15,
    #                'coin': 'ACA'}  # Should fail at creating stop loss as price is lower than current.
    # print(buy_details)
    # trader.handle_buy(buy_details)
    sell_details = {'sell_idx': 0, 'sell_price': 1.168, 'coin': 'ACA'}
    print(sell_details)
    trader.handle_sell(sell_details)


def run_trade(prod):
    print('@@@@ ----------->> prod', prod)
    trader = RealtimeTrade(prod=prod)
    show_portfolio_value(trader)
    # test_buy_stop_sell_works(trader)
    # test_buy_stop_sell_fails(trader)
    # trader.refresh_markets()


if __name__ == '__main__':
    run_trade(prod=True)
