from token import OP

from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import FuseAero, WingAero, AircraftAero
from acdesign.performance.propulsion import Propeller, Motor, Battery
from acdesign.performance.operating_point import OperatingPoint

from acdesign.performance.performance import Performance
from acdesign.airfoils.polar import UIUCPolars


clarky = UIUCPolars.local("CLARKYB")
sa7038 = UIUCPolars.local("SA7038")
e472 = UIUCPolars.local("E472")



buddiperf = Performance(
    AircraftAero(
        WingAero(3.6, 0.99876, [clarky,sa7038],[0, 0.2222, 1]),
        WingAero(0.98,0.2107,[e472],[0,1]),
        FuseAero(1.888,0.125),
        0.02, 3.6/3
    ),
    16, Propeller(), Motor(), Battery.lipo(12, 22.5)
)


def bperf(arspd):
    return buddiperf.calculate(OperatingPoint(Atmosphere.alt(0), arspd), 0)
    
perf = bperf(17)
print(perf.__dict__)