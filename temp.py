from acdesign.airfoils.polar import UIUCPolars
from acdesign.atmosphere import Atmosphere



pol = UIUCPolars.download("CLARKYB")

b = 1.205
c = 0.2
S = b * c
AR = b/c

u=12

atm = Atmosphere.alt(0)

mass = 1.2

re = atm.rho * u * c / atm.mu

import numpy as np


drg = pol.drag.loc[pol.drag.re == 60700]
Cd0 = drg.Cd.min()

import plotly.graph_objects as go


cls = np.linspace(-0.5, 1.5, 20)

k = 1 / (np.pi * AR )

cds = Cd0 + k * cls ** 2
fig = go.Figure()
fig.add_trace(go.Scatter(x=cls, y = cds, name="3D wing"))
fig.add_trace(go.Scatter(x=drg.Cl, y = drg.Cd, name = "2D Section"))

fig.update_layout(yaxis=dict(range=(0, 0.25), title="Cd"), xaxis=dict(title="Cl"))
fig.show()