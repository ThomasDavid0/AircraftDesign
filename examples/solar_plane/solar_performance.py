from acdesign.atmosphere import Atmosphere
from acdesign.solar_wing import SolarWing
from acdesign.airfoils.polar import UIUCPolar, available_sections
import numpy as np
from plotly.subplots import make_subplots
section = UIUCPolar.local("CLARKYB")

airspeed = np.array([12, 14, 16, 18, 20])

wing1 = SolarWing.straight(28, 2, section)
wing2 = SolarWing.double_taper(21, 15, 2, section)
wing3 = SolarWing.straight_to_elliptical(19, 18, 2, section)

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,)
wing1.plot(fig, row=1, col=1)
wing2.plot(fig, row=2, col=1)
wing3.plot(fig, row=3, col=1)


max_mass = wing3.max_mass(np.linspace(10, 20, 11), atm=Atmosphere.alt(0) )

fig.update_layout(
    template="plotly_white", 
    yaxis=dict(scaleanchor="x"),
    yaxis2=dict(scaleanchor="x"),
    yaxis3=dict(scaleanchor="x"),
    legend=dict(visible=False),
    width=900, height=500
)
#fig.show()

pass
#masses1 = wing1.max_mass(airspeed, atm=Atmosphere.alt(0))
#masses2 = wing2.max_mass(airspeed, atm=Atmosphere.alt(0))
#masses3 = wing3.max_mass(airspeed, atm=Atmosphere.alt(0))


