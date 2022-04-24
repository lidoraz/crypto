from plotly import graph_objects as go
from Indicators import SMA, FibMA, EMA


def add_moving_avgs(fig, ohlc, col='close', loc=1):
    lookaheads = [7, 25, 99]
    colors = ['orange', 'purple', 'cyan']
    for i in range(len(lookaheads)):
        ind = SMA(lookaheads[i], plot_loc=loc, color=colors[i])
        ind.calc(ohlc)
        ind.plot(fig)


def add_special_moving_avgs(fig, ohlc, col='close'):
    ind_fib = FibMA(14, color='Pink')
    ind_fib.calc(ohlc)
    ind_fib.plot(fig)

    ind_ema = EMA(14, color='Teal')
    ind_ema.calc(ohlc)
    ind_ema.plot(fig)
    # fig.add_trace(FibMA(ohlc, 25, col=col, color='Pink'), row=1, col=1)
    # fig.add_trace(EMA(ohlc, 25, col=col, color='Red'), row=1, col=1)
