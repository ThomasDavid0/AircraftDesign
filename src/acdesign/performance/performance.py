
import numpy as np
import pandas as pd

from acdesign.atmosphere import Atmosphere
from scipy.optimize import minimize, Bounds
from acdesign.performance.aero import FuseAero, WingAero, AircraftAero
from acdesign.performance.propulsion import Battery, Propeller, Motor, ConstantPropeller, FactorMotor, LookupPropeller, BUDDIMotor
from acdesign.performance.operating_point import OperatingPoint
from acdesign.performance.mass_estimation import estimate_mass
from acdesign.airfoils.polar import UIUCPolar
from dataclasses import dataclass


clarky = UIUCPolar.local("CLARKYB")
sa7038 = UIUCPolar.local("SA7038")
e472 = UIUCPolar.local("E472")



@dataclass
class Performance:
    aero: AircraftAero
    mass: float
    propeller: Propeller
    motor: Motor
    battery: Battery
    

    def calculate(self, op: OperatingPoint, wind: float, quick_trim = False) -> dict:
        # TODO include CG in trim
        trimfunc = self.aero.quick_trim if quick_trim else self.aero.trim
        trim = trimfunc(op, self.mass)

        
        cl = np.sum(trim.gCl)
        cd = np.sum(trim.gCd)
        
        stall = np.any(trim.stall)
        if stall:
            cd = 1
        
        drag = op.Q * self.aero.S * (cd + self.aero.cd0_offset)

        #TODO hard coded here to have two motors
        rpm, torque = self.propeller.calculate(drag/2, op.V, op.atm.rho)
        motor_efficiency = float(self.motor.efficiency(torque))
        preq = self.motor.calculate(rpm, torque) * 2 + 0.5*self.battery.v0  # adding 0.5A draw for other systems


        endurance = self.battery.endurance(preq) if not stall else 0

        range = (op.V - wind) * endurance
        

        #stall_speed = np.sqrt(2*9.81*self.mass/(1.225 * self.aero.S * self.aero.CLmax))
        cruise_stall_speed = np.sqrt(2*9.81*self.mass/(op.atm.rho * self.aero.S * self.aero.CLmax))
        
        return dict(
            mass=self.mass,
            wind=wind,
            AR=self.aero.wing.AR,
            b=self.aero.wing.b,
            S=self.aero.wing.S,
            drag=drag,
            rpm=rpm,
            torque=torque,
            motor_efficiency=motor_efficiency,
            preq=preq,
            endurance=endurance,
            range=range,
            stall=stall,
            cruise_stall_speed=cruise_stall_speed,
            cd=cd + self.aero.cd0_offset,
            cl=cl,
            **op.to_dict(),
            **pd.concat([trim.loc[t,:].add_prefix(f'{t}_') for t in trim.index]).to_dict(),
            **trim.iloc[:,-3:].sum().to_dict()
        )

    
    def optimum_speed(self, atm: Atmosphere, wind: float=0, target='range', quick_trim=False):

        def fn(v):
            return -self.calculate(OperatingPoint(atm, v), wind)[target]

        res = minimize(fn, 28, bounds=Bounds(10, 30), method='Nelder-Mead')

        return self.calculate(OperatingPoint(atm, res.x[0]), wind, quick_trim)


    @staticmethod
    def run(atm, V, b, S, cells, capacity, wind):

        aero = AircraftAero(
            WingAero(b, S, [clarky, clarky,sa7038],[0, 1/3, 1]),
            WingAero(0.2*S,np.sqrt(0.2*S/3.5),[e472],[0,1]),
            WingAero(0.1*S,np.sqrt(0.1*S/3.5),[e472],[0,1]),
            FuseAero(b/2.5,0.125),
            0.00, b/3, 
            cd0_offset=0
        )
        batt = Battery.lipo(cells, capacity)
        return Performance(
            aero, estimate_mass(aero, batt), 
            ConstantPropeller(1), 
            FactorMotor(0.325), 
            batt
        ).calculate(OperatingPoint(atm, V), wind, True)

    @staticmethod
    def optimize(atm: Atmosphere, vars: dict, consts: dict, cost: callable, **kwargs):
        from scipy.optimize import shgo
        def fn(vls):
            
            return cost(Performance.run(
                atm,
                **{key: vls[i] for i, key in enumerate(vars.keys())},
                **consts
            ))

        #res = minimize(fn, [v for v in vars.values()], **kwargs)
        res = shgo(fn, **kwargs)

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
        5000000 / perf['range'],
        50000 / perf['endurance'], 
        hard_limit(perf['cruise_stall_speed']+2, perf['v']),
        hard_limit(perf['stall_speed'], 15),
        hard_limit(perf['mass'], 16)

    ])



if __name__ == '__main__':



        
    perf = Performance(
        AircraftAero(
            WingAero(3.6, 0.6, [clarky,sa7038],[0, 0.2222, 1]), # 0.99876
            WingAero(0.98,0.2107,[e472],[0,1]),
            WingAero(0.375, 0.5*(0.25 + 0.14)*0.375,[e472],[0,1]),
            FuseAero(1.888,0.125),
            0.02, 3.6/3
        ),14, ConstantPropeller(1), FactorMotor(0.325), Battery.lipo(12, 22.5)
    )

    res = pd.DataFrame([perf.calculate(OperatingPoint(Atmosphere.alt(0), v), 0, False) for v in range(5, 30)])

    import plotly.express as px

    px.line(res, x='v', y=res.range, color='stall').show()