import numpy as np
import pandas as pd
import plotly.express as px
from mace0 import aircraft

from acdesign.atmosphere import Atmosphere
from acdesign.performance.propeller import ConstantPropeller, EmpiricalPropeller
from acdesign.performance.propulsion import FactorMotor, PropulsionSystem

propulsion = PropulsionSystem(
    propeller=EmpiricalPropeller(12*25.4/1000, 6*25.4/1000, 0.6),
    motor=FactorMotor(0.85),
)

l_over_d = pd.read_csv("examples/solar_plane/mace0/l_over_d.csv")

atm = Atmosphere.alt(0)

q = 0.5 * atm.rho * l_over_d.u**2
l_over_d = l_over_d.assign(
    drag= q * aircraft.S * (l_over_d.cd + 0.007),
)

l_over_d = l_over_d.assign(power=2*propulsion(atm, l_over_d.u, l_over_d.drag/2))

#px.line(l_over_d, x="u", y="power").show()

l_over_d.to_csv("examples/solar_plane/mace0/prediction.csv", index=False)