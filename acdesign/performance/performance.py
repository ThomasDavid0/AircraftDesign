
from token import OP
import numpy as np
import pandas as pd

from acdesign.atmosphere import Atmosphere
from scipy.optimize import minimize
from acdesign.performance.aero import FuseAero, WingAero, AircraftAero
from acdesign.performance.propulsion import Battery, Propeller, Motor
from acdesign.performance.operating_point import OperatingPoint
from acdesign.performance.mass_estimation import estimate_mass
from acdesign.airfoils.polar import UIUCPolars
from dataclasses import dataclass

clarky = UIUCPolars.local("CLARKYB")
sa7038 = UIUCPolars.local("SA7038")
e472 = UIUCPolars.local("E472")


@dataclass
class PerformanceResults:
    op: OperatingPoint
    wind: float
    trim: pd.DataFrame
    cl: float
    cd: float
    drag: float
    preq: float
    endurance: float
    range: float
    stall: bool
    stall_speed: float
    cruise_stall_speed: float


@dataclass
class Performance:
    aero: AircraftAero
    mass: float
    propeller: Propeller
    motor: Motor
    battery: Battery
    
    def calculate(self, op: OperatingPoint, wind: float, quick_trim = False):
        # TODO include CG in trim
        trim = self.aero.quick_trim(op, self.mass) if quick_trim else self.aero.trim(op, self.mass)

        cl = np.sum(trim.gCl)
        cd = np.sum(trim.gCd) 
        
        drag = op.Q * self.aero.S * cd

        #rpm, torque = self.propeller.calculate(op.atm, op.V, drag)
        #preq = self.motor.calculate(rpm, torque)

        preq = self.motor.calculate(self.propeller.calculate(op.V * drag))

        endurance = self.battery.endurance(preq)

        range = (op.V - wind) * endurance
        stall = cl > self.aero.CLmax

        stall_speed = np.sqrt(2*9.81*self.mass/(1.225 * self.aero.S * self.aero.CLmax))
        cruise_stall_speed = np.sqrt(2*9.81*self.mass/(op.atm.rho * self.aero.S * self.aero.CLmax))
        
        return PerformanceResults(
            op,wind,trim,cl,cd,drag,preq,endurance,
            range,stall,stall_speed,cruise_stall_speed
        )

    @staticmethod
    def run(atm, V, b, S, cells, capacity, wind):
        aero = AircraftAero(
            WingAero(b, S, [clarky,sa7038],[0, 1/3, 1]),
            WingAero(0.2*S,np.sqrt(0.2*S/3.5),[e472],[0,1]),
            FuseAero(b/2.5,0.125),
            0.02, b/3
        )
        batt = Battery.lipo(cells, capacity)
        return Performance(
            aero, estimate_mass(aero, batt), Propeller.factor(0.2), Motor.factor(0.9), batt
        ).calculate(OperatingPoint(atm, V),wind)

    @staticmethod
    def optimize(atm: Atmosphere, vars: dict, consts: dict, cost: callable, **kwargs):
        
        def fn(vls):
            return cost(Performance.build(
                atm,
                **{key: vls[i] for i, key in enumerate(vars.keys())},
                **consts
            ))

        res = minimize(fn, [v for v in vars.values()], **kwargs)

        res.perf = Performance.run(
                atm,
                **{key: res.x[i] for i, key in enumerate(vars.keys())},
                **consts
            )
        return res


def hard_limit(var, lim):
    return 50 * (var - lim)**2 if var > lim else 0


def cost(perf: Performance):
    return sum([
        2000000 / perf.range,
        100000 / perf.endurance, 
        hard_limit(perf.cruise_stall_speed+2, perf.op.V),
        hard_limit(perf.stall_speed, 15),
        hard_limit(perf.mass, 16)

    ])
    

if __name__ == '__main__':


    perfs = []
    for wind in np.linspace(0.0, 10.0, 5):
        
        res = Performance.optimize(
            Atmosphere.alt(3000),
            dict(b=4.0, S=4*0.2, V=25.0),
            dict(cells=10, capacity=25.5, wind=wind),
            cost=cost,
            bounds=[(3.5, 5.0), (0.2, 2.0), (5.0, 50.0)],
            #method="nelder-mead"
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
            "cruise stall speed (m/s)"
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