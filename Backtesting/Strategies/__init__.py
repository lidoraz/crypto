# from .utils import mark_enter_exit_points
# from Backtesting.Strategies.old.RSI_BB import RSIBB
# from Backtesting.Strategies.old.BB import BB
# from Backtesting.Strategies.old.MACross import MACross
# from Backtesting.Strategies.old.SMAStochRSI import SMAStochRSI
# from Backtesting.Strategies.old.SMAMACD import SMAMACD
# from Backtesting.Strategies.old.HighChange import HighChange
from .EMAVol import EMAVol
from .EMATrendSTC import EMATrendSTC
from .EMABB import EMABB
from .Strategy import Strategy
from .EMA3 import EMA3
from .S1 import S1
from .S2 import S2
from .S3 import S3
from .TheStrat import TheStrat

# TODO: Can calculate trend maybe better if taking this thing: over past 200 candles in 2 h period, get last value and first value, calculate their dervative, this is the trend.

All_STRATEGIES = dict(
    # RSIBB=RSIBB,
    # BB=BB,
    # MACROSS=MACross,
    # RSISTO=SMAStochRSI,
    # SMAMACD=SMAMACD,
    # HIGHCHANGE=HighChange,
    EMAVOL=EMAVol,
    EMATRENDSTC=EMATrendSTC,
    EMABB=EMABB,
    EMA3=EMA3,
    S1=S1,
    S2=S2,
    S3=S3,
    THESTRAT=TheStrat)
