from acdesign.atmosphere import Atmosphere
from acdesign.performance.operating_point import OperatingPoint
from acdesign.airfoils.polar import UIUCPolars
from acdesign.performance.aero import AircraftAero, WingAero, FuseAero

clarky = UIUCPolars.local("CLARKYB")
sa7038 = UIUCPolars.local("SA7038")
e472 = UIUCPolars.local("E472")

nrows=20
ncols=2

b = nrows * 0.14 + 1
C = ncols * 0.13 + 0.07
S = b * C

fus_length = b/4

aero = AircraftAero(
        WingAero(b, S, [clarky,sa7038],[0, 0.2222, 1]),
        WingAero(b*0.25, S*0.2, [e472],[0,1]),
        WingAero(b*0.15, S*0.1, [e472],[0,1]),
        FuseAero(fus_length, 0.05),
        0.02, fus_length * 0.75
    )


stall_speed = aero.stall_speed(Atmosphere.alt(0), 10)
print(stall_speed)