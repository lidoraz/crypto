from Realtime.Trade.utils.RealtimeTrade import RealtimeTrade
from Realtime.realtime_utils import handle_args
from Data import CryptoData
from Backtesting.Strategies import RSIBB, BB, MACross, SMAStochRSI, HighChange
from Realtime.realtime_utils import get_latest_buy_sell
from Utils.notify import TelegramBot
from Utils.utils import WaitToMinEveryHour, format_num
from tqdm import tqdm
import time


#  Working only with biannace at the momenet, take all the coins from the symbols, and filter only binance.
#  run only on those coins.
#  Use telegram to broadcast buy / sell commands, stright from the trader.

def get_broadcast_buy_sell_pct(result, strategy, timeframe):
    buys_txt = ""
    buy_str = f"🟢<b>Buy Status:</b> ({len(result['buy'])})\n"
    for res in sorted(result['buy'], key=lambda x :x['buy_pct_change'], reverse=True):
        buys_txt += f"{res['coin']} {format_num(res['buy_price'])}, {res['buy_pct_change']:0.2%}, ({format_num(res['sell_price_lose_stop'])}, {format_num(res['sell_price_win_stop'])})\n"
    nl = ""
    if len(buys_txt):
        buys_txt = buy_str + buys_txt[:-1]
        nl = "\n"
    sells_txt = ""
    sell_str = f"{nl}🔴<b>Sell Status:</b>({len(result['sell'])})\n"
    for res in sorted(result['sell'], key=lambda x: x['sell_pct_change'], reverse=False):
        sells_txt += f"{res['coin']} {format_num(res['sell_price'])}, {res['sell_pct_change']:0.2%}\n"
    if len(sells_txt):
        sells_txt = sell_str + sells_txt[:-1]
    broadcast_text = buys_txt + sells_txt
    if len(broadcast_text):
        broadcast_text = f'{strategy}({timeframe}) - PCT%\n' + broadcast_text
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


def broadcast():
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
    trigger_minutes = range(60)
    prod = parsed_args['prod']
    show_start_msg = parsed_args['show_start_msg']
    use_closed = False
    print(f'Checking Keys.. use_closed = {use_closed}')

    tb_notify = TelegramBot(prod=prod, verbose=0)
    print('Checking Keys.. All OK')
    strategy = HighChange({"pct": 0.015, 'vol_pct': 1.1})
    # strategy = MACross() # Will throw a lot of buy sells.
    print(f'-----> Strategy {strategy}, Trading every {timeframe}, at {trigger_minutes} min every hour')
    print(repr(strategy))
    if prod:
        print('-----> WARNING: $$$$ *PRODUCTION* - SLEEPING FOR 1 MIN')
        sleep_before()

    data_wrapper = CryptoData.get_wrapper(live=True,
                                          start_date='2022-06-01',
                                          only_exchange='binance')
    # FILTER OUT SYMBOLS, first run on very minimal set -> 5 coins at most from binance.
    symbols = data_wrapper.get_symbols()
    wait = WaitToMinEveryHour(trigger_minutes, offset_sec=5)
    start_msg = get_start_msg(symbols, timeframe, strategy)
    print(start_msg)
    if show_start_msg:
        tb_notify.send(start_msg)
    while True:
        if prod:
            wait.wait()
        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, symbols,
                                                                strategy, tf=timeframe, use_closed=use_closed)
        res = {'buy': buy_details_lst, 'sell': sell_details_lst}
        broadcast_text = get_broadcast_buy_sell_pct(res, strategy, timeframe)
        if broadcast_text:
            tb_notify.send(broadcast_text)

        if not prod:  # safety
            break


if __name__ == '__main__':
    broadcast()
