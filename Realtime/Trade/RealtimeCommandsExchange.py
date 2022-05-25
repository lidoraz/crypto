from Realtime.Trade.utils.RealtimeTrade import RealtimeTrade
from Realtime.realtime_utils import handle_args
from Data import CryptoData
from Backtesting.Strategies import RSIBB, BB, MACross
from Realtime.realtime_utils import get_latest_buy_sell
from Utils.notify import TelegramBot
from Utils.utils import WaitToMinEveryHour
from tqdm import tqdm
import time


# TODO:
#  Working only with biannace at the momenet, take all the coins from the symbols, and filter only binance.
#  run only on those coins.
#  Use telegram to broadcast buy / sell commands, stright from the trader.


def handle_buys_sells(buy_lst, sell_lst, trader: RealtimeTrade):
    res = {'buy': [], 'sell': []}
    for buy_details in buy_lst:
        code = trader.handle_buy(buy_details)
        print(f"Trader:: handle_buy - {buy_details['coin']} {code}")
        buy_details['trade_code'] = code
        res['buy'].append(buy_details)
    coins_in_stable_count = trader.get_assets_holding()
    for sell_details in sell_lst:
        coin = sell_details['coin']
        # double check as might be null
        if coins_in_stable_count and coin not in coins_in_stable_count:
            print(f'{coin} was listed to sell but holding less than min trade amount. code(-3)')
            continue
        code = trader.handle_sell(sell_details)
        print(f"Trader:: handle_sell - {coin} {code}")
        sell_details['trade_code'] = code
        res['sell'].append(sell_details)

    return res


def get_broadcast_buy_sell(result, strategy):
    # res = {'buy': [], 'sell': []}
    buys_txt = ""
    buy_str = "Buy Status:\n"
    for res in result['buy']:
        buys_txt += f"{res['coin']} p={res['buy_price']:.2f}, ({res['sell_price_lose_stop']:.2f}, {res['sell_price_win_stop']:.2f}), code({res['trade_code']})\n"
    nl = ""
    if len(buys_txt):
        buys_txt = buy_str + buys_txt[:-1]
        nl = "\n"
    sells_txt = ""
    sell_str = f"{nl}Sell Status:\n"
    for res in result['sell']:
        sells_txt += f"{res['coin']} p={res['sell_price']:.2f}, code({res['trade_code']})\n"
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
    start_msg = f'{title_strategy}\nFollowing: {str_symbols}'
    return start_msg


def sleep_before(time_sleep=60):
    print('Sleeping for 60 sec before starting....')
    for _ in tqdm(range(time_sleep)):
        time.sleep(1)


def realtime_exchange():
    """
    The active flag is typically used in ``currencies` <currency structure>` and ``markets` <market structure>`.
     The exchanges might put a slightly different meaning into it. If a currency is inactive, most of the time all corresponding tickers,
     orderbooks and other related endpoints return empty responses, all zeroes, no data or outdated information.
      The user should check if the currency is active and reload markets periodically.
    :return:
    """
    parsed_args = handle_args()
    timeframe = parsed_args['timeframe']
    trigger_minutes = parsed_args['trigger_minutes']
    prod = parsed_args['prod']
    show_start_msg = parsed_args['show_start_msg']
    print('Checking Keys..')
    trader = RealtimeTrade(prod)
    trader.exchange.checkRequiredCredentials()  # raises AuthenticationError
    tb_notify = TelegramBot(prod=prod, verbose=0)
    print('Checking Keys.. All OK')
    # generated 340% profit after 1.5 month.
    # strategy_params = dict(RSIBB_n_rsi_soon=7,
    #                        RSIBB_rsi_ahead=16,  # RSI over 10 becomes less sesitive but its not linear, like expo.
    #                        RSIBB_bb_ahead=12,
    #                        RSIBB_rsi_low=30,
    #                        RSIBB_rsi_high=70,
    #                        RSIBB_bb_std=2.16)

    # strategy = RSIBB(strategy_params)
    strategy = BB({'BB_ind_ahead': 20, 'BB_std': 2.0, 'BB_stop_lookahead': 70})
    # strategy = MACross() # Will throw a lot of buy sells.
    if prod:
        print(
            f'----------------> $$$$ Strategy {strategy}, Trading every {timeframe}, at {trigger_minutes} min every hour')
        sleep_before()
    else:
        print(f'-----> TEST Strategy {strategy}, Trading every {timeframe}, at {trigger_minutes} min every hour')

    data_wrapper = CryptoData.get_wrapper(live=True,
                                          start_date='2022-05-01',
                                          only_exchange=trader.exchange_name)
    # FILTER OUT SYMBOLS, first run on very minimal set -> 5 coins at most from binance.
    symbols = data_wrapper.get_symbols()
    wait = WaitToMinEveryHour(trigger_minutes)
    start_msg = get_start_msg(symbols, timeframe, strategy)
    print(start_msg)
    if show_start_msg:
        tb_notify.send(start_msg)
    while True:
        if prod:
            wait.wait()
        # trader.refresh_markets()
        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, symbols,
                                                                strategy, tf=timeframe)
        res = handle_buys_sells(buy_details_lst, sell_details_lst, trader)
        broadcast_text = get_broadcast_buy_sell(res, strategy)
        if broadcast_text:
            tb_notify.send(broadcast_text)

        if not prod:  # safety
            break


if __name__ == '__main__':
    realtime_exchange()
