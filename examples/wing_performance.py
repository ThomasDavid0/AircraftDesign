from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import WingPanel
import numpy as np
from acdesign.airfoils.polar import UIUCPolar
from acdesign.atmosphere import Atmosphere


atm = Atmosphere.alt(0)
cls=np.linspace(0, 1, 10)
v = np.full(cls.shape, 20)


section = UIUCPolar.local("E387A")

wing = Wing(
    [
        WingPanel.trapezoidal(1.5, 1.5 * 0.4, 1, 0.25),
        WingPanel.elliptical_cr(3, 0.4, 0.25),
    ]
)

loads, sloads = wing.run_avl(
    cls,
    ylocs=np.linspace(0, 1, 50),
    sections=[section] * 50
)


wingaero = wing.performance_wing(
    ylocs=[0, 1],
    polars=[section],
)

lift = wingaero.get_lift(atm, 20, cls) 

wing_results = wingaero(
    atm, v, lift, sloads[-1], n=50, mode="oto"
)

Cd = loads.CDind + wing_results.Cd0
drag = 0.5 * atm.rho * v**2 * wing.S * Cd
    
pass