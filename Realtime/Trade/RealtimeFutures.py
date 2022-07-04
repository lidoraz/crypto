# from Realtime.Trade.utils.RealtimeTrade import RealtimeTrade
# from Realtime.realtime_utils import handle_args
from Data import CryptoData
from Backtesting.Strategies import RSIBB, BB, MACross, SMAStochRSI, EMAVol
from Realtime.realtime_utils import get_latest_buy_sell_1min
from Utils.notify import TelegramBot
from Utils.utils import WaitToMinEveryHour, format_num
from tqdm import tqdm
import time


#  Working only with biannace at the momenet, take all the coins from the symbols, and filter only binance.
#  run only on those coins.
#  Use telegram to broadcast buy / sell commands, stright from the trader.


def handle_futures(buy_lst, sell_lst, trader):
    res = {'buy': [], 'sell': []}
    TRADE_USDT_AMOUNT = 20
    # coins_in_stable = trader.get_assets_holding(filter_min_trade=True)
    skip_coins = []
    for sell_details in sell_lst:
        coin = sell_details['coin']
        symbol = f'{coin}/USDT'
        sell_price = sell_details['sell_price']
        stop_price = sell_details['buy_price_lose_stop']
        amount = TRADE_USDT_AMOUNT / sell_price
        # (symbol, amount, side, stop_price, rw_ratio)
        code = trader.create_order(symbol, amount, 'sell', stop_price=stop_price, rw_ratio=1)
        print(f"Trader:: SHORT - {coin} {code}")
        sell_details['trade_code'] = code
        res['sell'].append(sell_details)
    if len(skip_coins):
        print(f'Listed to SELL, holding less than min trade amount. code(-3)({",".join(skip_coins)})')

    skip_coins = []
    for buy_details in buy_lst:
        coin = buy_details['coin']
        symbol = f'{coin}/USDT'
        sell_price = buy_details['buy_price']
        stop_price = buy_details['sell_price_lose_stop']
        amount = TRADE_USDT_AMOUNT / sell_price
        # (symbol, amount, side, stop_price, rw_ratio)
        code = trader.create_order(symbol, amount, 'buy', stop_price=stop_price, rw_ratio=1)
        print(f"Trader:: BUY - {coin} {code}")
        buy_details['trade_code'] = code
        res['buy'].append(buy_details)
    if len(skip_coins):
        print(f'Listed to BUY, already owning them. code(-11)({",".join(skip_coins)})')

    return res


def get_broadcast_buy_sell(result, strategy):
    buys_txt = ""
    buy_str = f"🟢<b>Long Status:</b> ({len(result['buy'])})\n"
    for res in result['buy']:
        buys_txt += f"{res['coin']} {format_num(res['buy_price'])}, ({format_num(res['sell_price_lose_stop'])}, {format_num(res['sell_price_win_stop'])}) ({res['trade_code']})\n"
    nl = ""
    if len(buys_txt):
        buys_txt = buy_str + buys_txt[:-1]
        nl = "\n"
    sells_txt = ""
    sell_str = f"{nl}🔴<b>Short Status:</b>({len(result['sell'])})\n"
    for res in result['sell']:
        sells_txt += f"{res['coin']} {format_num(res['sell_price'])} ({res['trade_code']})\n"
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


def realtime_long_short():
    """
    The active flag is typically used in ``currencies` <currency structure>` and ``markets` <market structure>`.
     The exchanges might put a slightly different meaning into it. If a currency is inactive, most of the time all corresponding tickers,
     orderbooks and other related endpoints return empty responses, all zeroes, no data or outdated information.
      The user should check if the currency is active and reload markets periodically.
    :return:
    """
    # parsed_args = handle_args()
    # timeframe = parsed_args['timeframe']
    # trigger_minutes = parsed_args['trigger_minutes']
    # prod = parsed_args['prod']
    # show_start_msg = parsed_args['show_start_msg']
    print('Checking Keys..')
    from binance_usdm_test import BinanceFutures
    prod = True

    trader = BinanceFutures(prod)
    trader.exchange.checkRequiredCredentials()  # raises AuthenticationError
    tb_notify = TelegramBot(prod=prod, verbose=0)
    print('Checking Keys.. All OK')
    # strategy_params = dict(
    #     aggressive=True,
    #     n_rsi_soon=4,
    #     rsi_ahead=10,  # RSI over 10 becomes less sesitive but its not linear, like expo.
    #     bb_ahead=20,
    #     rsi_low=30,
    #     rsi_high=70,
    #     bb_std=2.1)
    strategy = EMAVol()
    trigger_minutes = range(60)
    timeframe = '1T'
    print(f'-----> Strategy {strategy}, Trading every {timeframe}, at {trigger_minutes} min every hour')
    print(repr(strategy))
    if prod:
        print('-----> WARNING: $$$$ *PRODUCTION* - SLEEPING FOR 1 MIN')
        sleep_before()

    data_wrapper = CryptoData.get_wrapper(live=True,
                                          start_date='2022-05-01',
                                          only_exchange=trader.exchange_name)
    # FILTER OUT SYMBOLS, first run on very minimal set -> 5 coins at most from binance.
    # symbols = data_wrapper.get_symbols()
    # First try on few then on rest
    symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOGE'] #  'SHIB' is out as it has 1000x multiply
    # symbols = ['BTC']
    wait = WaitToMinEveryHour(trigger_minutes, offset_sec=5)
    start_msg = get_start_msg(symbols, timeframe, strategy)
    print(start_msg)
    # if show_start_msg:
    tb_notify.send(start_msg)
    use_closed = True
    while True:
        if prod:
            wait.wait()
        # trader.refresh_markets()
        buy_details_lst, sell_details_lst = get_latest_buy_sell_1min(data_wrapper, symbols,
                                                                strategy, tf=timeframe, n_candles_to_get=201)
        res = handle_futures(buy_details_lst, sell_details_lst, trader)
        broadcast_text = get_broadcast_buy_sell(res, strategy)
        if broadcast_text:
            tb_notify.send(broadcast_text)

        if not prod:  # safety
            break


if __name__ == '__main__':
    realtime_long_short()
