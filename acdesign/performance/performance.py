
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

        self.CL = self.mass * 9.81 / (self.op.Q * self.aero.S)
        self.CD = self.aero.CD0 + self.aero.k * self.CL**2

        self.D = self.op.Q * self.aero.S * self.CD
        self.preq = self.D * self.op.V
        self.endurance = self.mot.endurance(self.preq)
        self.range = (self.op.V - self.wind) * self.endurance
        self.stall = self.CL > self.aero.CLmax
        self.stall_speed = np.sqrt(2*9.81*self.mass/(1.225 * self.aero.S * self.aero.CLmax))
        self.cruise_stall_speed = np.sqrt(2*9.81*self.mass/(self.op.atm.rho * self.aero.S * self.aero.CLmax))

        
    @staticmethod
    def build(atm, V, b, S, CD0, CLmax, cells, capacity, wind):
        op = OperatingPoint(atm, V)
        aero = AeroModel(b, S, CD0, CLmax)
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
            cruise_stall_speed=self.cruise_stall_speed
        )

def hard_limit(var, lim):
    return 50 * (var - lim)**2 if var > lim else 0


def cost(perf: Performance):
    return sum([
        2000000 / perf.range,
        50000 / perf.endurance, 
        hard_limit(perf.cruise_stall_speed+2, perf.op.V),
        hard_limit(perf.stall_speed, 15),
        hard_limit(perf.mass, 16)

    ])
    

if __name__ == '__main__':

    perfs = []
    for wind in np.linspace(0.0, 20.0, 10):
        res = Performance.optimize(
            Atmosphere.alt(3000),
            dict(b=4.0, S=4*0.2, V=25.0),
            dict(CD0=0.02, CLmax=1.5, cells=10, capacity=25.5, wind=wind),
            cost=cost,
            bounds=[(2.0, 5.0), (0.2, 2.0), (5.0, 50.0)],
            method="nelder-mead"
        )
        perfs.append(res.perf)

    df = pd.DataFrame([p.dump() for p in perfs])

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        4,3,
        shared_xaxes=True,
        horizontal_spacing=0.05, 
        vertical_spacing=0.05,
        subplot_titles=(
            "AR", 
            "Span (m)", 
            "Wing Area (m**2)",
            "SMC (m)",
            "Mass (kg)", 
            "Airspeed (m/s)",
            "Range (km)",
            "Endurance (hr)",
            "stall speed (m/s)",
            "CD",
            "CL",
            "cruis stall speed (m/s)"
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
    atrace(df.wind, df.S, 1, 3)
    atrace(df.wind, df.S / df.b, 2, 1)
    atrace(df.wind, df.mass, 2, 2)    
    atrace(df.wind, df.V, 2, 3)
    atrace(df.wind, df.range, 3, 1)    
    atrace(df.wind, df.endurance, 3, 2)
    atrace(df.wind, df.stall_speed, 3, 3)
    atrace(df.wind, df.CD, 4, 1)    
    atrace(df.wind, df.CL, 4, 2)
    atrace(df.wind, df.cruise_stall_speed, 4, 3)    


    print(df)    
    fig.update_layout({
        "xaxis10":dict(title="Headwind Velocity (m/s)"), 
        "xaxis11":dict(title="Headwind Velocity (m/s)"),
        "xaxis12":dict(title="Headwind Velocity (m/s)")
        })

    fig.show()
    pass