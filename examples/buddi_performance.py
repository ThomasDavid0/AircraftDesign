



from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import FuseAero, WingAero, AircraftAero
from acdesign.performance.motor import Propulsion
from acdesign.performance.operating_point import OperatingPoint
from acdesign.performance.mass_estimation import estimate_mass
from acdesign.airfoils.polar import UIUCPolars
from acdesign.performance.performance import Performance, clarky, sa7038, e472
import numpy as np


b = 3.5
S = b*0.35
op = OperatingPoint(Atmosphere.alt(1000), 25)
aero = AircraftAero(
    WingAero(
        b, 
        S, 
        [clarky,sa7038],
        [0, 1/3, 1]
    ),
    WingAero(
        0.2*S,
        np.sqrt(0.2*S/3.5),
        [e472],
        [0,1]
    ),
    FuseAero(
        b/2.5,
        0.125
    ),
    0.02,
    b/3
)
mot = Propulsion.lipo(12, 22)
perf = Performance(op,aero,mot,16, 0)


pass