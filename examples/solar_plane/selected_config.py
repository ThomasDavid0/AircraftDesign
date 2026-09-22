from typing import Literal

import numpy as np
import plotly.graph_objects as go

from acdesign.airfoils.polar import UIUCPolar
from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import AircraftAero, FuseAero, WingAero
from acdesign.performance.operating_point import OperatingPoint
from acdesign.solar_wing import SolarWing

sg6041 = UIUCPolar.local("SG6041")
e472 = UIUCPolar.local("E472")

atm = Atmosphere.alt(0)
airspeed = np.linspace(7, 25, 42)
mass = 4.5
solarwing = SolarWing.straight_to_elliptical(19, 18, 2, sg6041)
wing = solarwing.aero
fus_length = 1.5



res = atm.rho * airspeed * wing.smc / atm.mu
cls = wing.get_cl(atm, airspeed, mass * 9.81)

n=10

avl_results = solarwing.wing.run_avl(cls, np.linspace(0, 1, n), [sg6041.airfoil()]*n )[0]


def get_alpha(cl, re):
    
    res = sg6041.apply(re=re, cl_or_alpha=cl / 0.9, mode="cl", mapping="oto")

    sg6041_df = sg6041.lookup(re=re, cl_or_alpha=cl / 0.9)
    if mode == "grid":
        return sg6041_df.alpha.to_numpy()
    else:
        pass

fig = go.Figure()
fig.add_trace(go.Scatter(x=avl_results["Alpha"], y=avl_results["Cl"], name="AVL Cl alpha"))
fig.add_trace(go.Scatter(x=get_alpha(cls, res), y=cls*0.9, name="UIUC 2D Cl alpha * 0.9", mode="lines"))
fig.update_layout(template="plotly_white", width=800, height=600).show()




aircraft = AircraftAero(
    wing,
    WingAero(wing.b * 0.2, wing.S * 0.2, [e472], [0, 1]),
    WingAero(wing.b * 0.1, wing.S * 0.1, [e472], [0, 1]),
    FuseAero(fus_length, 0.15),
    0.02,
    fus_length * 0.75,
)

res = aircraft.trim(
    atm,
    np.linspace(9, 22, 11),
    mass*9.81,
    mode="grid",
)

pass