# from .utils import mark_enter_exit_points
from .RSI_BB import RSIBB
from .BB import BB
from .MACross import MACross
from .SMAStochRSI import SMAStochRSI
from .SMAMACD import SMAMACD
from .HighChange import HighChange
from .EMAVol import EMAVol
from .EMATrendSTC import EMATrendSTC
from .EMABB import EMABB
from .Strategy import Strategy
from .EMA3 import EMA3

All_STRATEGIES = dict(RSIBB=RSIBB,
                      BB=BB,
                      MACROSS=MACross,
                      RSISTO=SMAStochRSI,
                      SMAMACD=SMAMACD,
                      HIGHCHANGE=HighChange,
                      EMAVOL=EMAVol,
                      EMATRENDSTC=EMATrendSTC,
                      EMABB=EMABB,
                      EMA3=EMA3)
