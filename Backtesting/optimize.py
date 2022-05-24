import pandas as pd
import itertools
from datetime import datetime
from tqdm import tqdm
from joblib import Parallel, delayed
import os

from Data import ProviderData
from Backtesting.Strategies import *

TIME_CONV = "%y%m%dT%H%M%S"


# TODO: How to handle multiple buys with buy price? and the stop losses?
class BacktestOptimizer:
    def __init__(self, provider: ProviderData, strategy: str, params, env_params):
        self.provider = provider
        self.symbols = sorted(provider.get_symbols())
        self.trades_str = []
        self.n_open_trades = 0
        # self.params = params
        self.tf = params['tf']
        self.start_budget = env_params['budget']
        self.free_balance = self.start_budget
        self.trade_value_stable = env_params['trade_value']
        self.min_trade = env_params['min_trade']
        self.trade_com = env_params['trade_com']
        self.dfs = []
        self.strategy_class = All_STRATEGIES[strategy.upper()](params)
        self.run_optimizer_ts = None
        self.trades_str = []

    def prepare_run_data(self):
        index_ts = None
        for i, symbol in enumerate(self.symbols):
            df = self.provider.get_data(symbol, self.tf)
            df = self.strategy_class.add_indicators(df)
            if index_ts is not None:
                if len(df.index) > len(index_ts):
                    index_ts = df.index
            else:
                index_ts = df.index
            self.dfs.append((symbol, df))
        self.run_optimizer_ts = index_ts

    def _handle_buy(self, curr_ts, row, symbol, context):
        if self.free_balance > self.trade_value_stable and not context['open']:
            buy_vars = self.strategy_class.act_buy(curr_ts, row)
            if not buy_vars:
                return None
            # buy_ts = buy_vars['buy_idx']
            context['open'] = True
            self.n_open_trades += 1
            buy_price = buy_vars['buy_price']
            buy_idx_vars = buy_vars
            context['n_buys'] += 1
            context['coin_amount'] += (self.trade_value_stable / (buy_price * (1 - self.trade_com)))
            trade_buy_value = self.trade_value_stable * (1 - self.trade_com)
            self.free_balance -= trade_buy_value
            context['t_buy_value'] += trade_buy_value
            context['buys'].append(dict(
                ts=curr_ts,
                price=buy_price,
                buy_value=trade_buy_value,
                win_stop=buy_idx_vars['sell_price_win_stop'],
                lose_stop=buy_idx_vars['sell_price_lose_stop']))
            return True

    def _handle_sell(self, curr_ts, row, symbol, context):
        sell_price = row['close']
        # context['coin_amount'] * sell_price >  # TODO check if this is needed
        if self.min_trade and context['open']:  # look if can sell
            sell_ts = curr_ts
            last_buy = context['buys'][-1]
            sell_price_win_stop = last_buy['win_stop']
            sell_price_lose_stop = last_buy['lose_stop']
            if sell_price > sell_price_win_stop:
                sold_cause = 'WIN_STOP'
                sold_price = sell_price_win_stop
                context['n_stopwins'] += 1
            elif sell_price < sell_price_lose_stop:
                sold_cause = 'LOSE_STOP'
                sold_price = sell_price_lose_stop
                context['n_stoploses'] += 1
            elif row['SELL_ALGO']:
                sold_cause = 'ALGO_SELL'
                sold_price = sell_price
                context['n_algosells'] += 1
            else:
                return
            context['open'] = False
            # buy_params
            buy_ts = last_buy['ts']  # last_buy = context['buys'][-1]
            buy_price = last_buy['price']
            buy_value = last_buy['buy_value']

            # value we get after selling all coins.

            sold_value = (context['coin_amount'] * sold_price) * (1 - self.trade_com)
            context['t_sell_value'] += sold_value
            profit = sold_value - buy_value
            profit_pct = (sold_price / buy_price) - 1
            context['coin_amount'] = 0  # assuming we always sell all
            # close trade
            # bought_value = last_buy['buy_value']
            # print(bought_value, sold_value)
            hours_holding = int((sell_ts - buy_ts).total_seconds() // 3600)
            self.n_open_trades -= 1
            self.free_balance += sold_value
            # CAN BE USED AS TRADE INFO
            TIME_CONV = "%d-%b,T%H:%M"
            trade = dict(
                sell_ts=curr_ts.strftime(TIME_CONV),
                buy_ts=buy_ts.strftime(TIME_CONV),
                symbol=symbol,
                cause=sold_cause,
                profit=f'{profit:.2f}',  # profit,
                profit_pct=f'{profit_pct:.2%}',  # profit_pct,
                buy_p=round(buy_price, 3),
                sold_p=round(sold_price, 3),
                hours_holding=hours_holding,
                sold_value=round(sold_value, 3),
                balance=round(self.free_balance, 3))
            context['sells'].append(trade)
            # trade = dict(symbol=symbol, sold_cause=sold_cause, buy_price=buy_price,
            #              sold_price=round(sold_price, 3),
            #              buy_ts=buy_ts.strftime(TIME_CONV), sell_ts=sell_ts.strftime(TIME_CONV),
            #              hours_holding=hours_holding,
            #              profit=f'{profit:.2f}', profit_pct=f'{profit_pct:.2%}', budget=f'{self.budget:.2f}')
            last_buy['ts'] = buy_ts.strftime(TIME_CONV)
            return last_buy, trade

    def get_assets_valuation(self, _dict, at_idx=None):
        assets = {sym: v['coin_amount'] for sym, v in _dict.items() if v['coin_amount'] > 0}
        if at_idx is None:
            assets_price = {sym: df.iloc[-1]['close'] for sym, df in self.dfs if sym in assets.keys()}
        else:
            assets_price = {sym: df.loc[at_idx]['close'] for sym, df in self.dfs if sym in assets.keys()}
        assets_valuation = {k: v * assets_price[k] for k, v in assets.items()}
        assets_valuation_sum = sum(assets_valuation.values())
        return assets_valuation_sum, assets

    def get_dict(self):
        _dict = {
            symbol: dict(n_buys=0, n_algosells=0, n_stopwins=0, n_stoploses=0, open=False, coin_amount=0, t_buy_value=0,
                         t_sell_value=0, buys=[], sells=[]) for symbol in self.symbols}
        return _dict

    def run(self):
        self.prepare_run_data()
        history = []
        counter = dict()
        n_buys = 0
        n_algosells = 0
        n_stopwins = 0
        n_stoploses = 0
        _dict = self.get_dict()
        for curr_ts in self.run_optimizer_ts:
            if self.n_open_trades == 0 and self.free_balance < 0:
                print('budget is over try again.')
                break
            for symbol, df in self.dfs:
                if curr_ts not in df.index:
                    continue
                context = _dict[symbol]
                row = df.loc[curr_ts]
                is_buy = self._handle_buy(curr_ts, row, symbol, context)
                if not is_buy:
                    res = self._handle_sell(curr_ts, row, symbol, context)
                    if res:
                        buy_info, sell_info = res
                        print(str(sell_info).replace("'", '').replace(' ', '\t'))
                        # history.append(dict(symbol=symbol, BUY=buy_info, SELL=sell_info))
        for symbol, context in _dict.items():
            n_buys += context['n_buys']
            n_algosells += context['n_algosells']
            n_stopwins += context['n_stopwins']
            n_stoploses += context['n_stoploses']
        # print(history)
        assets_valuation_sum, assets = self.get_assets_valuation(_dict)
        run_results = dict(free_balance=round(self.free_balance, 3), assets_valuation=round(assets_valuation_sum, 3),
                           n_open=self.n_open_trades,
                           n_buys=n_buys, n_algosells=n_algosells, n_stopwins=n_stopwins, n_stoploses=n_stoploses,
                           assets=assets)
        # def dict_prict(d):
        #     def conv(v):
        #         if isinstance(float, v):
        #             return round(v, 3)
        #     for k,v in d.items():

        print(run_results)
        total_balance = round(self.free_balance + assets_valuation_sum, 3)
        print(
            f'run: Starting={self.start_budget}, After: balance={self.free_balance :0.2f} + asset={assets_valuation_sum:0.2f}\n'
            f' profits: {total_balance - self.start_budget :0.2f}, pct={(total_balance / self.start_budget) - 1 :0.2%}')
        return total_balance, self.n_open_trades, self.trades_str, run_results


def run_optimizer(provider: ProviderData, strategy: str, params, env_params):
    op = BacktestOptimizer(provider, strategy, params, env_params)
    return op.run()


def find_optimal_strategy(provider: ProviderData, start_date, strategy: str, optimized_params: dict, n_jobs=8):
    budget = 250
    trade_value = max(int(0.05 * budget), 11)
    assert trade_value >= 11, 'trade_value must be higher than 10, increase budget'
    env_params = dict(budget=budget, trade_value=trade_value, min_trade=10, trade_com=0.001)  # trade_v = 25
    print('---> env_params =', env_params)
    time_start = datetime.now()
    # filter out not relevant params:
    keys_to_remove = [k for k in optimized_params if not k.startswith(strategy) and k not in ['tf']]
    optimized_params = {k: optimized_params[k] for k in optimized_params if k not in keys_to_remove}
    print(f'Finding optimal strategies with these params:', optimized_params.keys())
    # iterate permutation with dicts: https://stackoverflow.com/questions/38721847/how-to-generate-all-combination-from-values-in-dict-of-lists-in-python
    keys, values = zip(*optimized_params.items())
    permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    # TODO: Preloaded is needed for the multiprocessing to avoid multiple access for DB, try how to solve this
    provider_loaded = provider.get_offline_wrapper(tfs=optimized_params['tf'])
    print('Running with n_jobs:', n_jobs)
    if n_jobs == 1:
        print('Debug Mode..')
        job_results = []
        for params in tqdm(permutations_dicts):
            job_results.append(run_optimizer(provider_loaded, strategy, params, env_params=env_params))
    else:
        job_results = Parallel(n_jobs=n_jobs)(
            delayed(run_optimizer)(provider_loaded, strategy, params, env_params=env_params) for params in
            tqdm(permutations_dicts))

    metric = 'total_balance'

    l_trades_str = []
    res = []
    for params, job_result in zip(permutations_dicts, job_results):
        total_balance, n_open_trades, trades_str, run_results = job_result
        params[metric] = total_balance
        params['n_trades'] = len(trades_str)
        params['n_open_trades'] = n_open_trades
        l_trades_str.append(trades_str)
        res.append(params)  # budget, open_trades, trades_str, _dict
        # TODO: fix this
        # def print_n_trades(_dict):
        #     res = [(sym, ([(k, v[k]) for k in v if k.startswith('n_')])) for sym, v in _dict.items()]
        #     res = sorted(res) # sorts by key
        #     print(res)
        #     return res
        #
        # print_n_trades(run_results)

    df = pd.DataFrame(res)
    df = df.sort_values(metric, ascending=False)
    # [print(sym,([v[k] for k in v if k.startswith('n_')])) for sym,v in _dict.items()] print n_Buys #todo
    # get win strategy:
    win_idx = df.index[0]
    budget_after = df[metric].iloc[0]
    win_trades = l_trades_str[win_idx]
    print('Index:', win_idx)
    print('Params:', df.iloc[0].to_dict())
    print(f'Budget PROFIT: {budget_after - budget:}, pct: {(budget_after - budget) - 1}')
    for trade in win_trades:
        print(trade)
    print("Total trades:", len(win_trades))

    # save df
    time = datetime.now()
    print(f"TIME TOOK: {int((time - time_start).total_seconds() / 60)} min")
    name = f'{time.strftime(TIME_CONV)}_{start_date}_{provider.name}_{strategy}'

    output_path = 'Backtesting/strategy_output/'
    os.makedirs(output_path, exist_ok=True)

    full_path_summary = output_path + name + '_summary.csv'
    full_path_trades = output_path + name + '_trades.tsv'
    df.to_csv(full_path_summary)
    with open(full_path_trades, 'w') as f:
        for trade in win_trades:
            print(trade, file=f)
