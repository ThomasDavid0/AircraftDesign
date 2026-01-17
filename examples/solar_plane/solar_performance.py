from acdesign.atmosphere import Atmosphere
from acdesign.solar_wing import SolarWing, SolarWingResults
from acdesign.airfoils.polar import UIUCPolar
import numpy as np
import pandas as pd
import plotly.graph_objects as go

section = UIUCPolar.local("CLARKYB")


wing = SolarWing.straight_to_elliptical(19, 18, 2, section)

results = SolarWingResults.build(
    wing, np.linspace(5, 20, 16), np.linspace(10, 25, 21), Atmosphere.alt(9000), "pchip"
)

fig = go.Figure()
newmasses = np.linspace(5, 20, 100)
newairspeeds = np.linspace(10, 25, 100)
newmasses, newairspeeds = np.meshgrid(newmasses, newairspeeds)
newZ = results.power_interpolator((newmasses, newairspeeds))
fig.add_trace(
    go.Scatter3d(
        x=newmasses.flatten(),
        y=newairspeeds.flatten(),
        z=newZ.flatten(),
        mode="markers",
        marker=dict(size=1, color="black"),
    )
)

fig.add_trace(
    go.Scatter3d(
        x=[5, 20, 20, 5, 5],
        y=[5, 5, 25, 25, 5],
        z=[wing.solar_power] * 5,
        mode="lines",
        line=dict(color="black", width=5),
        name="Boundary",
    )
)

fig.update_layout(
    template="plotly_white",
    scene=dict(
        xaxis=dict(title="Mass (kg)", range=[5, 20]),
        yaxis=dict(title="Airspeed (m/s)", range=[5, 25]),
        zaxis=dict(title="Power (W)", range=[0, wing.solar_power * 2]),
    ),
)

masses = results.get_mass(np.linspace(10, 25, 100), wing.solar_power)

fig.add_trace(
    go.Scatter3d(
        x=masses.mass,
        y=masses.airspeed,
        z=masses.power,
        mode="lines",
        line=dict(color="blue", width=5),
        name="Max Mass at Solar Power",
    )
)

fig.show()
pass
