from acdesign.performance.performance import Performance
from acdesign.performance.aero import AeroModel
from acdesign.performance.motor import Propulsion
from acdesign.performance.operating_point import OperatingPoint
from acdesign.atmosphere import Atmosphere
import numpy as np
import pandas as pd


atm = Atmosphere.alt(0)


perfs = []
for mass in np.linspace(0.1,5, 10):
    perf = Performance(
        OperatingPoint(atm, 10),
        AeroModel(1.206, 0.3, 0.03, 1.5),
        Propulsion.lipo(3, 1200),
        mass,#1.345, 
        0
    )
    perfs.append(perf)


df = pd.DataFrame([p.dump() for p in perfs])
print(df)
import plotly.graph_objects as go
#
#
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.CD, y=df.CL))
fig.show()