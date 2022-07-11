import pandas as pd
import itertools
from datetime import datetime
from tqdm import tqdm
from joblib import Parallel, delayed
import os

from Data import ProviderData
from Backtesting.Strategies import *

TIME_CONV = "%y-%m-%dT%H:%M"


def update_trade_stats(run_dict):
    stats = dict(n_trades=0, n_buys=0, n_sells=0, n_stopwins=0, n_stoploses=0)
    for symbol, context in run_dict.items():
        stats['n_buys'] += context['n_buys']
        stats['n_sells'] += context['n_sells']
        stats['n_stopwins'] += context['n_stopwins']
        stats['n_stoploses'] += context['n_stoploses']
    stats['n_trades'] = sum(stats.values())
    return stats


# def dict_prict(d):
#     def conv(v):
#         if isinstance(float, v):
#             return round(v, 3)
#     for k,v in d.items():

# TODO: How to handle multiple buys with buy price? and the stop losses?
class BacktestOptimizer:
    def __init__(self, provider: ProviderData, strategy: Strategy, params, env_params):
        self.provider = provider
        self.symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOGE']
        # self.symbols = sorted(provider.get_symbols())
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
        self.strategy = strategy
        self.run_optimizer_ts = None
        self.trades_str = []
        self.verbose = env_params['verbose']

    def prepare_run_data(self):
        index_ts = None
        for i, symbol in enumerate(self.symbols):
            df = self.provider.get_data(symbol, self.tf)
            df = self.strategy.add_indicators(df)
            if index_ts is not None:
                if len(df.index) > len(index_ts):
                    index_ts = df.index
            else:
                index_ts = df.index
            self.dfs.append((symbol, df))
            if self.verbose:
                print(f'Added indicators for {symbol} ({i+1}/{len(self.symbols)})')
        self.run_optimizer_ts = index_ts

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
            symbol: dict(posSide=None, n_buys=0, n_sells=0, n_stopwins=0, n_stoploses=0, coin_amount=0, total_buy_value=0,
                         total_sell_value=0, pos_buys=[], pos_sells=[], trades=[]) for symbol in self.symbols}
        return _dict

    def _handle_buy(self, curr_ts, row, context):
        if self.free_balance > self.trade_value_stable and context['posSide'] is None:
            buy_vars = self.strategy.act_buy(curr_ts, row)
            if not buy_vars:
                return False
            buy_price = buy_vars['buy_price']
            fee = self.trade_value_stable * self.trade_com
            buy_value_net = self.trade_value_stable - fee
            context['coin_amount'] += (buy_value_net / buy_price)
            self.free_balance -= self.trade_value_stable
            context['total_buy_value'] += buy_value_net
            context['pos_buys'].append(dict(
                ts=curr_ts,
                price=buy_price,
                buy_value=buy_value_net,
                win_stop=buy_vars['sell_price_win_stop'],
                lose_stop=buy_vars['sell_price_lose_stop']))
            context['posSide'] = 'BUY'
            context['n_buys'] += 1
            self.n_open_trades += 1
            return True
        return False

    def _handle_sell(self, curr_ts, row, context):
        if self.free_balance > self.trade_value_stable and context['posSide'] is None:  # look if can sell
            sell_vars = self.strategy.act_sell(curr_ts, row)
            if not sell_vars:
                return False
            sell_price = sell_vars['sell_price']
            fee = self.trade_value_stable * self.trade_com
            sell_value = self.trade_value_stable - fee
            context['coin_amount'] += sell_value / sell_price  # Maybe should minus as its short
            self.free_balance -= self.trade_value_stable
            context['total_sell_value'] += sell_value
            context['pos_sells'].append(dict(
                ts=curr_ts,
                price=sell_price,
                sell_value=sell_value,
                win_stop=sell_vars['buy_price_win_stop'],
                lose_stop=sell_vars['buy_price_lose_stop']))
            context['posSide'] = 'SELL'
            context['n_sells'] += 1
            self.n_open_trades += 1
            return True
        return False

    def _close_pos(self, curr_ts, row, symbol, context):
        side = context['posSide']
        assert side in ('BUY', 'SELL')
        low = row['low']
        high = row['high']
        cause = None
        buy_price = None
        sell_price = None
        if side == 'BUY':
            last_buy = context['pos_buys'][-1]
            if low > last_buy['lose_stop'] and high < last_buy['win_stop']:
                return None
            elif high >= last_buy['win_stop']:
                cause = 'WIN_STOP'
                sell_price = last_buy['win_stop']
                context['n_stopwins'] += 1
            elif low <= last_buy['lose_stop']:
                cause = 'LOSE_STOP'
                sell_price = last_buy['lose_stop']
                context['n_stoploses'] += 1
            else:
                print('Wrong state')
            pos_ts = last_buy['ts']
            buy_value = last_buy['buy_value']
            buy_price = last_buy['price']
            sell_value_gross = (context['coin_amount'] * sell_price) * (1 - self.trade_com)
            fee = sell_value_gross * self.trade_com
            sell_value = sell_value_gross - fee
        else:
            last_sell = context['pos_sells'][-1]
            if low > last_sell['win_stop'] and high < last_sell['lose_stop']:
                return None
            elif high >= last_sell['lose_stop']:
                cause = 'LOSE_STOP'
                buy_price = last_sell['lose_stop']
                context['n_stoploses'] += 1
            elif low <= last_sell['win_stop']:
                cause = 'WIN_STOP'
                buy_price = last_sell['win_stop']
                context['n_stopwins'] += 1
            else:
                print('Wrong state')
            pos_ts = last_sell['ts']
            sell_value = last_sell['sell_value']
            sell_price = last_sell['price']
            buy_value_gross = (context['coin_amount'] * buy_price)
            fee = buy_value_gross * self.trade_com
            buy_value = buy_value_gross - fee
        context['posSide'] = None
        profit = round(sell_value - buy_value, 2)
        profit_pct = round((sell_price / buy_price) - 1, 4)  # ROI
        context['coin_amount'] = 0  # assuming we always sell all
        # close trade
        min_holding = (curr_ts - pos_ts).total_seconds() // 60
        self.n_open_trades -= 1
        self.free_balance += sell_value
        # CAN BE USED AS TRADE INFO
        trade = dict(
            side=side,
            entry_ts=pos_ts.strftime(TIME_CONV),
            exit_ts=curr_ts.strftime(TIME_CONV),
            symbol=symbol,
            cause=cause,
            profit=f'{profit:.2f}',  # profit,
            profit_pct=f'{profit_pct:.2%}',  # profit_pct,
            buy_p=round(buy_price, 3),
            sold_p=round(sell_price, 3),
            min_holding=min_holding,
            sold_value=round(sell_value, 3),
            balance=round(self.free_balance, 3))
        context['trades'].append(trade)
        return trade

    def run(self):
        self.prepare_run_data()
        _dict = self.get_dict()
        for curr_ts in self.run_optimizer_ts:
            if self.n_open_trades == 0 and self.free_balance < self.min_trade:
                print('budget is over try again.')
                break
            for symbol, df in self.dfs:
                if curr_ts not in df.index:
                    continue
                context = _dict[symbol]
                row = df.loc[curr_ts]
                # check if pos it closed
                if context['posSide']:
                    trade = self._close_pos(curr_ts, row, symbol, context)
                    if trade:
                        print_str = str(trade).replace("'", '').replace(' ', '\t')[1:-1]  # maybe use json
                        self.trades_str.append(print_str)
                        if self.verbose:
                            print(print_str)

                if context['posSide']:  # has position
                    continue
                is_buy = self._handle_buy(curr_ts, row, context)
                is_sell = False
                if not is_buy:
                    is_sell = self._handle_sell(curr_ts, row, context)
                # if is_sell or is_buy:
                #     print(curr_ts, symbol, is_sell, is_buy)

        assets_valuation_sum, assets = self.get_assets_valuation(_dict)
        trade_stats = update_trade_stats(_dict)
        total_balance = round(self.free_balance + assets_valuation_sum, 3)
        total_profit = round(total_balance - self.start_budget, 2)
        total_profit_pct = round((total_balance / self.start_budget) - 1, 4)
        run_results = dict(
            profit=total_profit,
            profit_pct=total_profit_pct,
            total_balance=total_balance,
            free_balance=round(self.free_balance, 3),
            assets_valuation=round(assets_valuation_sum, 3),
            **trade_stats,
            n_open=self.n_open_trades)
        # print(f'\nrun: Starting at={self.start_budget} ==> {total_balance}'
        #       f'(balance={self.free_balance :0.2f},asset={assets_valuation_sum:0.2f})'
        #       f' stats={trade_stats}, n_open={self.n_open_trades}\n'
        #       f'Profits: {total_balance - self.start_budget :0.2f}, pct={(total_balance / self.start_budget) - 1 :0.2%}')
        return run_results, self.trades_str, assets


def run_optimizer(provider: ProviderData, strategy_name: str, params, env_params):
    strategy = All_STRATEGIES[strategy_name.upper()](params)
    op = BacktestOptimizer(provider, strategy, params, env_params)
    run_results, trades_str, assets = op.run()
    print(f'#strategy= {repr(strategy)}\n'
          f'res={run_results}')
    return run_results, trades_str, assets


def find_optimal_strategy(provider: ProviderData, start_date, strategy: str, optimized_params: dict, n_jobs=8):
    budget = 250
    trade_value = 40
    comm = 0.001  # 0.001
    # trade_value = max(int(0.05 * budget), 11)
    assert trade_value >= 11, 'trade_value must be higher than 10, increase budget'
    env_params = dict(budget=budget, trade_value=trade_value, min_trade=40, trade_com=comm,
                      verbose=0 if n_jobs > 1 else 1)  # trade_v = 25
    print('---> env_params =', env_params)
    time_start = datetime.now()
    print(f'Finding optimal strategies with these params:', optimized_params.keys())
    # iterate permutation with dicts: https://stackoverflow.com/questions/38721847/how-to-generate-all-combination-from-values-in-dict-of-lists-in-python
    keys, values = zip(*optimized_params.items())
    permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    # get offline so it is loaded only once
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

    metric = 'profit_pct'
    l_trades_str = []
    res = []
    for params, job_result in zip(permutations_dicts, job_results):
        run_res, trades_str, assets = job_result
        params.update(run_res)
        l_trades_str.append(trades_str)
        res.append(params)

    df = pd.DataFrame(res)
    df = df.sort_values(metric, ascending=False)
    # [print(sym,([v[k] for k in v if k.startswith('n_')])) for sym,v in _dict.items()] print n_Buys #todo
    # get win strategy:
    win_idx = df.index[0]
    win_trades = l_trades_str[win_idx]
    win_row = df.iloc[0]
    print('Index:', win_idx)
    print(f'Total Portfoio Balance: PROFIT: {win_row["profit"]:0.2f},'
          f' pct: {win_row["profit_pct"]:.2%}')

    # if n_jobs > 1:
    #     for trade in win_trades:
    #         print(trade)
    #     print("Total trades:", len(win_trades))

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

    common_cols = [
        'total_balance',
        'profit',
        'profit_pct',
        'free_balance',
        'assets_valuation',
        'n_trades',
        'n_buys',
        'n_sells',
        'n_stopwins',
        'n_stoploses', ]
    best_run = df.iloc[0][common_cols]
    # best_run[metric] = best_run[metric].apply(lambda x: f'{x:.2%}')
    # best_run.name = str(strategy)
    return str(strategy), best_run.to_dict()
    # return win_portfolio_balance
