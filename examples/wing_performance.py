from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import WingPanel
import numpy as np
from acdesign.airfoils.polar import UIUCPolar

section = UIUCPolar.local("CLARKYB")

wing = Wing(
    [
        WingPanel.trapezoidal(1.5, 1.5 * 0.4, 1, 0.25),
        #WingPanel.trapz_crct(3, 0.4, 0.2, 0.25),
        WingPanel.elliptical_cr(3, 0.4, 0.25),
    ]
)

loads, sloads = wing.run_avl(
    cls=np.linspace(0, 1, 5),
    ylocs=np.linspace(0, 1, 50),
    sections=[section] * 50
)


pass