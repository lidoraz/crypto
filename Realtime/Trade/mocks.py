from pandas import Timestamp


def mock_binance_market_buy(idx=1):
    # real trade and filled, it took about 5 sec to fill, maybe it is better to make it async.
    trades_details = [{'info': {'symbol': 'ACAUSDT', 'orderId': '28375570', 'orderListId': '-1',
                                'clientOrderId': 'x-R4BD3S8238ac023a3de1bcbe727da4', 'transactTime': '1652738144191',
                                'price': '0.00000000', 'origQty': '23.25000000', 'executedQty': '23.25000000',
                                'cummulativeQuoteQty': '10.99725000', 'status': 'FILLED', 'timeInForce': 'GTC',
                                'type': 'MARKET',
                                'side': 'BUY'}, 'id': '28375570', 'clientOrderId': 'x-R4BD3S8238ac023a3de1bcbe727da4',
                       'timestamp': 1652738144191, 'datetime': '2022-05-16T21:55:44.191Z', 'lastTradeTimestamp': None,
                       'symbol': 'ACA/USDT', 'type': 'market', 'timeInForce': 'IOC', 'postOnly': False, 'side': 'buy',
                       'price': 0.473,
                       'stopPrice': None, 'amount': 23.25, 'cost': 10.99725, 'average': 0.473, 'filled': 23.25,
                       'remaining': 0.0,
                       'status': 'closed', 'fee': None, 'trades': [], 'fees': []},
                      {'info': {'symbol': 'CRVUSDT', 'orderId': '806304733', 'orderListId': '-1',
                                'clientOrderId': 'x-R4BD3S82271682f43e0329ffdeb0a1', 'transactTime': '1652985063594',
                                'price': '0.00000000', 'origQty': '10.20000000', 'executedQty': '10.20000000',
                                'cummulativeQuoteQty': '11.91360000', 'status': 'FILLED', 'timeInForce': 'GTC',
                                'type': 'MARKET',
                                'side': 'BUY'}, 'id': '806303959', 'clientOrderId': 'x-R4BD3S82fd7279cb67c13b8e5e011c',
                       'timestamp': 1652985013730, 'datetime': '2022-05-19T18:30:13.730Z', 'lastTradeTimestamp': None,
                       'symbol': 'CRV/USDT', 'type': 'market', 'timeInForce': 'IOC', 'postOnly': False, 'side': 'buy',
                       'price': 1.164,
                       'stopPrice': None, 'amount': 10.2, 'cost': 11.8728, 'average': 1.164, 'filled': 10.2,
                       'remaining': 0.0,
                       'status': 'closed', 'fee': None, 'trades': [], 'fees': []}
                      ]
    return trades_details[idx]


def mock_binance_market_sell(idx=0):
    # Took less than 1 sec, probably because there was a demand.
    # Need to note that there was about 0.000001 amount still left in binance.
    # rework persistance trades.
    trades_details = [{'info': {'symbol': 'ACAUSDT', 'orderId': '28376579', 'orderListId': '-1',
                                'clientOrderId': 'x-R4BD3S82498ae75dbc0c972f222c0', 'transactTime': '1652739173276',
                                'price': '0.00000000', 'origQty': '23.22000000', 'executedQty': '23.22000000',
                                'cummulativeQuoteQty': '11.07594000', 'status': 'FILLED', 'timeInForce': 'GTC',
                                'type': 'MARKET', 'side': 'SELL'}, 'id': '28376579',
                       'clientOrderId': 'x-R4BD3S82498ae75dbc0c972f222c0', 'timestamp': 1652739173276,
                       'datetime': '2022-05-16T22:12:53.276Z', 'lastTradeTimestamp': None, 'symbol': 'ACA/USDT',
                       'type': 'market', 'timeInForce': 'IOC', 'postOnly': False, 'side': 'sell', 'price': 0.477,
                       'stopPrice': None, 'amount': 23.22, 'cost': 11.07594, 'average': 0.477, 'filled': 23.22,
                       'remaining': 0.0, 'status': 'closed', 'fee': None, 'trades': [], 'fees': []},
                      {'info': {'symbol': 'GALUSDT', 'orderId': '74907173', 'orderListId': '-1',
                                'clientOrderId': 'x-R4BD3S826a435edfc89a8bb84a1cf0', 'transactTime': '1652980435229',
                                'price': '0.00000000', 'origQty': '1.99800000', 'executedQty': '1.99800000',
                                'cummulativeQuoteQty': '12.12985800', 'status': 'FILLED', 'timeInForce': 'GTC',
                                'type': 'MARKET',
                                'side': 'SELL'}, 'id': '74907173', 'clientOrderId': 'x-R4BD3S826a435edfc89a8bb84a1cf0',
                       'timestamp': 1652980435229, 'datetime': '2022-05-19T17:13:55.229Z', 'lastTradeTimestamp': None,
                       'symbol': 'GAL/USDT', 'type': 'market', 'timeInForce': 'IOC', 'postOnly': False, 'side': 'sell',
                       'price': 6.071,
                       'stopPrice': None, 'amount': 1.998, 'cost': 12.129858, 'average': 6.071, 'filled': 1.998,
                       'remaining': 0.0,
                       'status': 'closed', 'fee': None, 'trades': [], 'fees': []}]
    return trades_details[idx]


def mock_binance_limit_buy():
    trade_details = {'info': {'symbol': 'ACAUSDT', 'orderId': '28375120', 'orderListId': '-1',
                              'clientOrderId': 'x-R4BD3S8261e93d43339c961a2ccc88', 'transactTime': '1652737648232',
                              'price': '0.23700000', 'origQty': '42.28000000', 'executedQty': '0.00000000',
                              'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC',
                              'type': 'LIMIT',
                              'side': 'BUY'}, 'id': '28375120', 'clientOrderId': 'x-R4BD3S8261e93d43339c961a2ccc88',
                     'timestamp': 1652737648232, 'datetime': '2022-05-16T21:47:28.232Z', 'lastTradeTimestamp': None,
                     'symbol': 'ACA/USDT', 'type': 'limit', 'timeInForce': 'GTC', 'postOnly': False, 'side': 'buy',
                     'price': 0.237,
                     'stopPrice': None, 'amount': 42.28, 'cost': 0.0, 'average': None, 'filled': 0.0,
                     'remaining': 42.28,
                     'status': 'open', 'fee': None, 'trades': [], 'fees': []}
    return trade_details


def mock_binance_create_sell_stop_loss():
    return {'info': {'symbol': 'CRVUSDT', 'orderId': '806311786', 'orderListId': '-1',
                     'clientOrderId': 'x-R4BD3S8286727613927dc110a91112', 'transactTime': '1652985502608',
                     'price': '1.04900000', 'origQty': '10.20000000', 'executedQty': '0.00000000',
                     'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC',
                     'type': 'STOP_LOSS_LIMIT',
                     'side': 'SELL', 'stopPrice': '1.04900000'}, 'id': '806311786',
            'clientOrderId': 'x-R4BD3S8286727613927dc110a91112', 'timestamp': 1652985502608,
            'datetime': '2022-05-19T18:38:22.608Z', 'lastTradeTimestamp': None, 'symbol': 'CRV/USDT',
            'type': 'stop_loss_limit', 'timeInForce': 'GTC', 'postOnly': False, 'side': 'sell', 'price': 1.049,
            'stopPrice': 1.049, 'amount': 10.2, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 10.2,
            'status': 'open', 'fee': None, 'trades': [], 'fees': []}


def mock_binance_cancel_stop_loss():
    return {'info': {'symbol': 'GALUSDT', 'origClientOrderId': 'ios_70ea0441ea7c454480e639bec571cde0',
                     'orderId': '73498205',
                     'orderListId': '-1', 'clientOrderId': 'Ov1yu7iUs3ngrimVpIfVDb', 'price': '5.02000000',
                     'origQty': '1.99800000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000',
                     'status': 'CANCELED', 'timeInForce': 'GTC', 'type': 'STOP_LOSS_LIMIT', 'side': 'SELL',
                     'stopPrice': '5.03000000'}, 'id': '73498205', 'clientOrderId': 'Ov1yu7iUs3ngrimVpIfVDb',
            'timestamp': None, 'datetime': None, 'lastTradeTimestamp': None, 'symbol': 'GAL/USDT',
            'type': 'stop_loss_limit',
            'timeInForce': 'GTC', 'postOnly': False, 'side': 'sell', 'price': 5.02, 'stopPrice': 5.03, 'amount': 1.998,
            'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 1.998, 'status': 'canceled', 'fee': None,
            'trades': [],
            'fees': []}


def mock_binance_sell_oco():
    # returns as raw data
    return {'orderListId': '66615880', 'contingencyType': 'OCO', 'listStatusType': 'EXEC_STARTED',
            'listOrderStatus': 'EXECUTING', 'listClientOrderId': 'sDAknO7Wcm2qJ0ev8LMeE0',
            'transactionTime': '1653034422433',
            'symbol': 'ACAUSDT',
            'orders': [{'symbol': 'ACAUSDT', 'orderId': '28994334', 'clientOrderId': 'hdK8vQMI5RcUfbvkb8WGGs'},
                       {'symbol': 'ACAUSDT', 'orderId': '28994335', 'clientOrderId': 'Tnvdxy73U5vFUOBBmNddMa'}],
            'orderReports': [{'symbol': 'ACAUSDT', 'orderId': '28994334', 'orderListId': '66615880',
                              'clientOrderId': 'hdK8vQMI5RcUfbvkb8WGGs', 'transactTime': '1653034422433',
                              'price': '0.34000000', 'origQty': '30.80000000', 'executedQty': '0.00000000',
                              'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC',
                              'type': 'STOP_LOSS_LIMIT', 'side': 'SELL', 'stopPrice': '0.35000000'},
                             {'symbol': 'ACAUSDT', 'orderId': '28994335', 'orderListId': '66615880',
                              'clientOrderId': 'Tnvdxy73U5vFUOBBmNddMa', 'transactTime': '1653034422433',
                              'price': '0.45000000', 'origQty': '30.80000000', 'executedQty': '0.00000000',
                              'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC',
                              'type': 'LIMIT_MAKER', 'side': 'SELL'}]}


def mock_buy_data():
    arr = [{'buy_idx': 0, 'buy_price': 0.465, 'sell_price_win_stop': 0.48, 'sell_price_lose_stop': 0.453, 'coin': 'ACA',
            'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel')},
           {'buy_idx': 0, 'buy_price': 8.1075, 'sell_price_win_stop': 8.3559, 'sell_price_lose_stop': 7.8652,
            'coin': 'APE',
            'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel')},
           {'buy_idx': 0, 'buy_price': 1.37, 'sell_price_win_stop': 1.39, 'sell_price_lose_stop': 1.327, 'coin': 'CRV',
            'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel', )},
           {'buy_idx': 0, 'buy_price': 93.32, 'sell_price_win_stop': 95.05, 'sell_price_lose_stop': 89.16,
            'coin': 'EGLD',
            'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel', )},
           {'buy_idx': 0, 'buy_price': 2025.43, 'sell_price_win_stop': 2060.09, 'sell_price_lose_stop': 1979.12,
            'coin': 'ETH', 'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel', )},
           {'buy_idx': 0, 'buy_price': 1.45105, 'sell_price_win_stop': 1.47593, 'sell_price_lose_stop': 1.4,
            'coin': 'GMT',
            'ts': Timestamp('2022-05-16 22:25:00+0300', tz='Israel')}]
    return arr


def mock_sell_data():
    arr = [{'coin': 'SHIB', 'sell_price': 0.00812999, 'ts': Timestamp('2022-05-18 19:45:00+0300', tz='Israel')},
           {'coin': 'ACA', 'sell_price': 0.4, 'ts': Timestamp('2022-05-19 14:45:00+0300', tz='Israel')},
           {'coin': 'GAL', 'sell_price': 5.74, 'ts': Timestamp('2022-05-19 14:45:00+0300', tz='Israel')}]
    return arr
