
from token import OP
import numpy as np
import pandas as pd

from acdesign.atmosphere import Atmosphere
from scipy.optimize import minimize

class AeroModel:
    def __init__(self, b, S, MAC, CD0, CLmax):
        self.b = b
        self.S = S
        self.MAC = MAC
        self.CD0 = CD0
        self.CLmax = CLmax

    @property
    def AR(self):
        return self.b / self.MAC

    @property
    def k(self):
        return 1 / (np.pi * self.AR)


class Propulsion:
    def __init__(self, capacity, v0, eta, n):
        self.capacity = capacity
        self.eta = eta
        self.v0 = v0
        self.n = n

    @staticmethod
    def lipo(cells, Ah):
        return Propulsion(0.85 * Ah * 60 * 60, cells*4.0, 0.3, 1.3)

    def endurance(self, preq):
        return ((self.eta * self.v0 * self.capacity / preq ) ** self.n ) * 3600 ** (1 - self.n)

    @property
    def Ah(self):
        return self.capacity / (60*60*0.85)

    @property
    def mass(self):
        return self.Ah * self.v0 * 0.0049 

    @property
    def lipo_cells(self):
        return self.v0 / 4.0


class OperatingPoint:
    def __init__(self, atm: Atmosphere, V: float):
        self.atm = atm
        self.V = V

    @property
    def Q(self):
        return 0.5 * self.atm.rho * self.V**2


def estimate_mass(aero: AeroModel, batt: Propulsion):
    #      constant + kg/m + kg/Wh
    return 6 + 0.5 * aero.b**2 + aero.AR / 10 + batt.mass

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
    def build(atm, V, b, S, MAC, CD0, CLmax, cells, capacity, wind):
        op = OperatingPoint(atm, V)
        aero = AeroModel(b, S, MAC, CD0, CLmax)
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
            c4=self.c4
        )
    
    @property
    def c1(self):
        return 1000000 / self.range
    @property
    def c2(self):
        return 1000 if self.stall else 0 

    @property
    def c3(self):
        return 1000 if self.stall_speed > 15 else 0
    
    @property
    def c4(self):
        return 100000 / self.endurance


if __name__ == '__main__':


    def cost(perf: Performance):
        return perf.c1 + perf.c2 + perf.c3 + perf.c4

    perfs = []
    for wind in np.linspace(0.0, 20.0, 10):
        res = Performance.optimize(
            Atmosphere.alt(3000),
            dict(b=4.0, S=0.8, MAC=0.3, V=25.0),
            dict(CD0=0.001, CLmax=1.5, cells=6, capacity=68.0, wind=wind),
            cost=cost,
            bounds=[(2.0, 5.0), (0.3, 2.0), (0.2, 0.5), (5.0, 50.0)],
            method="nelder-mead"
        )
        perfs.append(res.perf)

    df = pd.DataFrame([p.dump() for p in perfs])
    pass