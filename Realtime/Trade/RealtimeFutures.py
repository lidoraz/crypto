from binance_usdm_test import BinanceFutures
# from Realtime.realtime_utils import handle_args
from Data import CryptoData
from Backtesting.Strategies import RSIBB, BB, MACross, SMAStochRSI, EMAVol, EMA3
from Realtime.realtime_utils import get_latest_buy_sell_futures, handle_args_1min
from Utils.notify import TelegramBot
from Utils.utils import WaitToMinEveryHour, format_num
from tqdm import tqdm
import time


def handle_futures(buy_lst, sell_lst, trader):
    res = {'buy': [], 'sell': []}
    # BTC TRADE MUST BE HIGHER THAN 30
    # TODO: INSERT THIS TO CODE, Some coins have less amount after precision check
    TRADE_USDT_AMOUNT = 40
    # coins_in_stable = trader.get_assets_holding(filter_min_trade=True)
    skip_coins = []
    for sell_details in sell_lst:
        coin = sell_details['coin']
        symbol = f'{coin}/USDT'
        if trader.has_position(symbol):
            skip_coins.append(coin)
            continue
        coin_amount_to_buy = TRADE_USDT_AMOUNT / sell_details['sell_price']
        code = trader.create_order(symbol, 'sell', coin_amount_to_buy,
                                   sell_details['buy_price_lose_stop'],
                                   sell_details['buy_price_win_stop'])
        print(f"Trader:: SHORT - {coin} {code}")
        sell_details['trade_code'] = code
        res['sell'].append(sell_details)
    if len(skip_coins):
        print(f'Listed to SELL and already in position code(-2)({",".join(skip_coins)})')

    skip_coins = []
    for buy_details in buy_lst:
        coin = buy_details['coin']
        symbol = f'{coin}/USDT'
        if trader.has_position(symbol):
            skip_coins.append(coin)
            continue
        coin_amount_to_buy = TRADE_USDT_AMOUNT / buy_details['buy_price']
        code = trader.create_order(symbol, 'buy', coin_amount_to_buy, buy_details['sell_price_lose_stop'],
                                   buy_details['sell_price_win_stop'])
        print(f"Trader:: BUY - {coin} {code}")
        buy_details['trade_code'] = code
        res['buy'].append(buy_details)
    if len(skip_coins):
        print(f'Listed to BUY and already in position code(-2)({",".join(skip_coins)})')

    return res


def get_broadcast_buy_sell(result, strategy):
    buys_txt = ""
    buy_str = f"🟢<b>Long Status:</b> ({len(result['buy'])})\n"
    for res in result['buy']:
        buys_txt += f"{res['coin']} {format_num(res['buy_price'])}, (sl={format_num(res['sell_price_lose_stop'])}, tp={format_num(res['sell_price_win_stop'])}) ({res['trade_code']})\n"
    nl = ""
    if len(buys_txt):
        buys_txt = buy_str + buys_txt[:-1]
        nl = "\n"
    sells_txt = ""
    sell_str = f"{nl}🔴<b>Short Status:</b>({len(result['sell'])})\n"
    for res in result['sell']:
        sells_txt += f"{res['coin']} {format_num(res['sell_price'])}, (sl={format_num(res['buy_price_lose_stop'])}, tp={format_num(res['buy_price_win_stop'])}) ({res['trade_code']})\n"
    if len(sells_txt):
        sells_txt = sell_str + sells_txt[:-1]
    broadcast_text = buys_txt + sells_txt
    if len(broadcast_text):
        broadcast_text = f'{strategy}\n' + broadcast_text
        return broadcast_text
    return None


def get_start_msg(symbols, timeframe, strategy):
    title_strategy = f'{strategy}({timeframe})'
    str_symbols = ", ".join(symbols)
    start_msg = f'{title_strategy}\n{repr(strategy)}\nFollowing: {str_symbols}'
    return start_msg


def sleep_before(time_sleep=60):
    print('Sleeping for 60 sec before starting....')
    for _ in tqdm(range(time_sleep)):
        time.sleep(1)


def get_trigger_minutes(tf):
    if tf == '1H':
        return [0]
    if tf[-1] == 'T':
        tf = int(tf.split('T')[0])
        return list(range(0, 60, tf))
    return ValueError('tf type not supported (1Min to 1Hour only)')


def realtime_long_short():
    """
    The active flag is typically used in ``currencies` <currency structure>` and ``markets` <market structure>`.
     The exchanges might put a slightly different meaning into it. If a currency is inactive, most of the time all corresponding tickers,
     orderbooks and other related endpoints return empty responses, all zeroes, no data or outdated information.
      The user should check if the currency is active and reload markets periodically.
    :return:
    """
    parsed_args = handle_args_1min()
    prod = parsed_args['prod']
    show_start_msg = parsed_args['show_start_msg']
    print('Checking Keys..')
    trader = BinanceFutures(prod)
    trader.exchange.checkRequiredCredentials()  # raises AuthenticationError
    tb_notify = TelegramBot(prod=prod, verbose=0)
    print('Checking Keys.. All OK')
    # positive profit.. of 7.5$ after a month...
    # timeframe = '5T'
    # 5T,200,3,14,20,20,1.2
    # 1H,100,14,25,1,20,1.0 # PROFIT: 38.01, pct: 15.20% from 2022-05-01 to 2022-07-12
    ################
    # timeframe = '1H'
    # strategy_params = dict(
    #     ema_ahead=100,
    #     n_ema_soon=14,
    #     ema_fast_ahead=25,
    #     vol_ema=1,
    #     support_ahead=20,
    #     risk_reward=1.0)
    ################
    # TODO: add tf and strategy name into the configuration for easy changing strategies.
    # timeframe = '5T'
    # strategy_params = {"ema_ahead": 200, "n_ema_soon": 3, "ema_fast_ahead": 14, "vol_ema": 20, "support_ahead": 20, "risk_reward": 1.2}
    strategy_params = {'tf': '2H', 'ema_slow_lk': 200, 'ema_mid_lk': 30, "risk_reward": 2.0, "support_ahead": 5, "vol_pct": 0.05}
    timeframe = strategy_params['tf']

    strategy = EMA3(strategy_params)
    trigger_minutes = get_trigger_minutes(timeframe)

    print(f'-----> Strategy {strategy}, Trading every {timeframe}, at {trigger_minutes} min every hour')
    print(repr(strategy))
    if prod:
        print('-----> WARNING: $$$$ *PRODUCTION* - SLEEPING FOR 1 MIN')
        sleep_before()

    data_wrapper = CryptoData.get_wrapper(live=True,
                                          only_exchange=trader.exchange_name)
    symbols = data_wrapper.get_symbols()
    # First try on few then on rest
    # Solana has minimum of 40USD for a trade in futures.
    # symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOGE']  # 'SHIB' is out as it has 1000x multiply
    wait = WaitToMinEveryHour(trigger_minutes, offset_sec=5)
    start_msg = get_start_msg(symbols, timeframe, strategy)
    print(start_msg)
    if show_start_msg:
        tb_notify.send(start_msg)
    while True:
        if prod:
            wait.wait()
        buy_details_lst, sell_details_lst = get_latest_buy_sell_futures(data_wrapper, symbols,
                                                                        strategy, tf=timeframe, n_candles_to_get=201)
        res = handle_futures(buy_details_lst, sell_details_lst, trader)
        broadcast_text = get_broadcast_buy_sell(res, strategy)
        if broadcast_text:
            tb_notify.send(broadcast_text)

        if not prod:  # safety
            break
        # Need to find a way for create an OCO order for stop-loss orders, currently reduce-only works okay.
        # trader.remove_unlocked_positions(symbols)


if __name__ == '__main__':
    realtime_long_short()
