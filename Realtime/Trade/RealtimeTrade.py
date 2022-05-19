from Realtime.Trade.mocks import *
from Realtime.Trade.persistence_trades import PersistenceTrades
import ccxt
import os


# TODO: ADD check if symbol is active, along with refresh to the markets.
class RealtimeTrade:
    def _check_init(self):
        if self.stable_coin_min_amount > self.stable_coin_trade_amount or self.stable_coin_min_amount < 10:
            raise ValueError('stable_coin values not valid')
        if os.environ.get('BINANCE_API') is None or os.environ.get('BINANCE_SECRET') is None:
            raise EnvironmentError('API / Secret not set')

    def __init__(self, prod):
        # self.db = PersistenceTrades(db_path)
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
        print(f'Init exchange: {self.exchange_name}')

    def refresh_markets(self):
        # need to be loaded periodically !!
        # This is done in ccxt every create / cancel/ order
        try:
            self.exchange.load_markets()
            print('Refreshed markets')
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

        # order_details['id']
        # order_details['timestamp']
        # order_details['price']
        # order_details['amount']
        # order_details['filled']
        # order_details['remaining']
        # order_details['stopPrice']
        # order_details['type'] # market
        # order_details['side'] # buy

    def _add_order_to_db(self, symbol, order_details):
        trade_id = order_details['id']
        price = order_details['price']
        stopPrice = order_details['stopPrice']
        amount_requested = order_details['amount']
        amount_filled = order_details['filled']
        type = order_details['type']
        side = order_details['side']
        status = order_details['status']
        order_dt = order_details['datetime']
        #  exchange, symbol, buy_price, amount
        details = dict(order_dt=order_dt, type=type, side=side, status=status, symbol=symbol, price=price,
                       stopPrice=stopPrice, amount_requested=amount_requested,
                       amount_filled=amount_filled, exchange=self.exchange_name, trade_id=trade_id)
        print('Adding to DB:', type, side, details)
        if self.is_production:
            with open('order_history.txt', 'a') as fp:
                print(details, file=fp)
        # self.db.add_trade(self.exchange_name, trade_id, type, side, symbol, price, amount, amount_filled)

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

    def _create_buy_market(self, coin, buy_price, stop_loss_price):
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
            self._add_order_to_db(symbol, order_details)
            self._create_stop_loss_request(coin, stop_loss_price, order_details)
        except Exception as e:
            print(self.exchange_name, symbol, f'failed create MARKET-BUY order:', type(e).__name__, str(e))

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
            print(f'Warning: Canceled more than {len(order_details)} order for {symbol}')
            for order_details in order_details:
                self._add_order_to_db(symbol, order_details)
        else:
            self._add_order_to_db(symbol, order_details)

    def _create_sell_market(self, coin, sell_price):
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
            self._add_order_to_db(symbol, order_details)
        except Exception as e:
            print(self.exchange_name, symbol, f'failed create MARKET-SELL order:', type(e).__name__, str(e))

    def _create_stop_loss_request(self, coin, stop_price, order_details):
        # TODO: Add sleep here, could be it needs some time to update. Follow that if it continues
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

    def handle_buy(self, buy_details):
        coin = buy_details['coin']
        buy_price = buy_details['buy_price']
        stop_loss_price = buy_details['sell_price_lose_stop']
        self._create_buy_market(coin, buy_price, stop_loss_price)

    def handle_sell(self, sell_details):
        coin = sell_details['coin']
        sell_price = sell_details['sell_price']
        self._create_sell_market(coin, sell_price)


def show_portfolio_value(trader):
    all_holding_usdt = trader.get_assets_holding()
    print(all_holding_usdt)


def test_buy_stop_sell_works(trader):
    buy_details = {'buy_idx': 0, 'buy_price': 1.168, 'sell_price_win_stop': 1.28, 'sell_price_lose_stop': 1.05,
                   'coin': 'CRV'}
    print(buy_details)
    trader.handle_buy(buy_details)
    sell_details = {'sell_idx': 0, 'sell_price': 1.168, 'coin': 'CRV'}
    print(sell_details)
    trader.handle_sell(sell_details)


def test_buy_stop_sell_fails(trader):
    # Fails at setting stoploss, but then sells the asset.
    buy_details = {'buy_idx': 0, 'buy_price': 1.168, 'sell_price_win_stop': 1.28, 'sell_price_lose_stop': 1.05,
                   'coin': 'ACA'}  # Should fail at creating stop loss as price is lower than current.
    print(buy_details)
    trader.handle_buy(buy_details)
    sell_details = {'sell_idx': 0, 'sell_price': 1.168, 'coin': 'ACA'}
    print(sell_details)
    trader.handle_sell(sell_details)


def run_trade():
    prod = True
    print('@@@@ ----------->> prod', prod)
    trader = RealtimeTrade(prod=prod)

    show_portfolio_value(trader)
    test_buy_stop_sell_works(trader)
    # trader.refresh_markets()


if __name__ == '__main__':
    run_trade()
