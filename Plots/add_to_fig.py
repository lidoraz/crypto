from plotly import graph_objects as go
from Indicators import SMA


def add_moving_avgs(fig, ohlc, col='close', loc=1):
    lookaheads = [7, 25, 99]
    colors = ['orange', 'purple', 'cyan']
    for i in range(len(lookaheads)):
        ind = SMA(lookaheads[i], plot_loc=loc)
        ind.calc(ohlc)
        ind.plot(fig, colors[i])

# def add_special_moving_avgs(fig, ohlc, col='close'):
#     fig.add_trace(get_FibMAD(ohlc, 25, col=col, color='Pink'), row=1, col=1)
#     fig.add_trace(get_EMA(ohlc, 25, col=col, color='Red'), row=1, col=1)
