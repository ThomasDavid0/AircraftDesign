
from token import OP
import numpy as np
import pandas as pd

from acdesign.atmosphere import Atmosphere
from scipy.optimize import minimize
from acdesign.performance.aero import AeroModel
from acdesign.performance.motor import Propulsion
from acdesign.performance.operating_point import OperatingPoint
from acdesign.performance.mass_estimation import estimate_mass


class Performance:
    def __init__(self, op: OperatingPoint, aero: AeroModel, mot: Propulsion, mass: float, wind:float):
        self.op = op
        self.aero = aero
        self.mot = mot
        self.mass = mass
        self.wind=wind

    @property
    def CL(self):
        return self.mass * 9.81 / (self.op.Q * self.aero.S)

    @property
    def CD(self):
        return self.aero.CD0 + self.aero.k * self.CL**2

    @property
    def D(self):
        return self.op.Q * self.aero.S * self.CD

    @property
    def preq(self):
        return self.D * self.op.V

    @property
    def endurance(self):
        return self.mot.endurance(self.preq)
    
    @property
    def range(self):
        return (self.op.V - self.wind) * self.endurance

    @property
    def stall(self):
        return self.CL > self.aero.CLmax

    @property
    def stall_speed(self):
        return np.sqrt(2*9.81*self.mass/(self.op.atm.rho * self.aero.S * self.aero.CLmax))
   
    @staticmethod
    def build(atm, V, b, MAC, CD0, CLmax, cells, capacity, wind):
        op = OperatingPoint(atm, V)
        aero = AeroModel(b, b*MAC, MAC, CD0, CLmax)
        mot = Propulsion.lipo(cells, capacity)
        return Performance(op,aero,mot,estimate_mass(aero, mot), wind)

    @staticmethod
    def optimize(atm: Atmosphere, vars: dict, consts: dict, cost: callable, **kwargs):
        
        def fn(vls):
            return cost(Performance.build(
                atm,
                **{key: vls[i] for i, key in enumerate(vars.keys())},
                **consts
            ))

        res = minimize(fn, [v for v in vars.values()], **kwargs)

        res.perf = Performance.build(
                atm,
                **{key: res.x[i] for i, key in enumerate(vars.keys())},
                **consts
            )
        return res

    def dump(self):
        return dict(
            b=self.aero.b,
            S=self.aero.S,
            MAC=self.aero.MAC,
            AR=self.aero.AR,
            CD0=self.aero.CD0,
            CLMax=self.aero.CLmax,
            mass=self.mass,
            cells=self.mot.lipo_cells,
            capacity=self.mot.Ah,
            wind=self.wind,
            V=self.op.V,
            CL=self.CL,
            CD=self.CD,
            endurance=self.endurance / (60*60),
            range=self.range / 1000,
            stall_speed=self.stall_speed,
            c1=self.c1,
            c2=self.c2,
            c3=self.c3,
            c4=self.c4,
            c5=self.c5,
        )
    
    @property
    def c1(self):
        return 2000000 / self.range
    @property
    def c2(self):
        safety=2
        return 5000 * (self.stall_speed-self.op.V)**2 if (self.stall_speed + safety) > self.op.V else 0

    @property
    def c3(self):
        lim=15
        return 5000 * (self.stall_speed-lim)**2 if self.stall_speed > lim else 0

    @property
    def c4(self):
        return 100000 / self.endurance

    @property
    def c5(self):
        lim=16
        return 5000 * (self.mass - lim)**2 if self.mass > lim else 0



if __name__ == '__main__':

    def cost(perf: Performance):
        return perf.c1 + perf.c2 + perf.c3 + perf.c4 + perf.c5

    perfs = []
    for wind in np.linspace(0.0, 20.0, 10):
        res = Performance.optimize(
            Atmosphere.alt(3000),
            dict(b=4.0, MAC=0.3, V=25.0),
            dict(CD0=0.01, CLmax=1.5, cells=6, capacity=51.0, wind=wind),
            cost=cost,
            bounds=[(2.0, 5.0), (0.2, 0.5), (5.0, 50.0)],
            method="nelder-mead"
        )
        perfs.append(res.perf)

    df = pd.DataFrame([p.dump() for p in perfs])

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        4,2,
        shared_xaxes=True,
        horizontal_spacing=0.05, 
        vertical_spacing=0.05,
        subplot_titles=(
            "AR", 
            "Span (m)", 
            "Wing Area (m**2)",
            "MAC (m)",
            "Mass (kg)", 
            "Airspeed (m/s)",
            "Range (km)",
            "Endurance (hr)"
        )
    ).update_layout(margin=dict(l=20, r=20, t=40, b=40))

    def atrace(x,y, r, c):
        fig.add_trace(go.Scatter(
            x=x, 
            y=y, 
            showlegend=False,
            line=dict(color="black"),
            marker=dict(color="black"), 
        ), row=r, col=c)

    atrace(df.wind, df.AR, 1, 1)
    atrace(df.wind, df.b, 1, 2)
    atrace(df.wind, df.S, 2, 1)
    atrace(df.wind, df.MAC, 2, 2)
    atrace(df.wind, df.mass, 3, 1)    
    atrace(df.wind, df.V, 3, 2)
    atrace(df.wind, df.range, 4, 1)    
    atrace(df.wind, df.endurance, 4, 2)
    print(df)    
    fig.update_layout({
        "xaxis7":dict(title="Headwind Velocity (m/s)"), 
        "xaxis8":dict(title="Headwind Velocity (m/s)")
        })

    fig.show()
    pass