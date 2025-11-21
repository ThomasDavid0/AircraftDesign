
from typing import Any
from acdesign.atmosphere import Atmosphere
from .propeller import Propeller, ConstantPropeller, LookupPropeller
import numpy as np
import pandas as pd
from dataclasses import dataclass
import numpy.typing as npt


@dataclass
class Battery:
    capacity: float
    v0: float
    n: float

    @staticmethod
    def lipo(cells, Ah):
        return Battery(Ah * 60 * 60, cells*4.0, 1.3)

    def endurance(self, preq):
        return ((self.v0 * self.capacity * 0.85 / preq ) ** self.n ) * 3600 ** (1 - self.n)

    @property
    def Ah(self):
        return self.capacity / (60*60*0.85)

    @property
    def lipo_cells(self):
        return self.v0 / 4.0
    


class Motor:
    def calculate(self, rpm, torque):
        return 2 * np.pi * torque * rpm / 60

    def __call__(self, rpm, torque):
        return pd.DataFrame(dict(power =self.calculate(rpm, torque)))

@dataclass
class FactorMotor(Motor):
    factor: float = 0.65

    def efficiency(self, torque):
        
        return np.full(torque.shape, self.factor)

    def calculate(self, rpm, torque):
        return 2 * np.pi * torque * (rpm / 60) / self.factor
    


@dataclass
class PropulsionSystem:
    propeller: Propeller
    motor: Motor

    def __call__(self, atm: Atmosphere, airspeed: npt.ArrayLike, thrust: float) -> npt.ArrayLike:
        rpm, torque = self.propeller.calculate(thrust, airspeed, atm.rho)
        power = self.motor.calculate(rpm, torque)
        return power



data=np.array([
[0.0028486974173058677, 0.07876561182546382],
[0.008567939287711712, 0.11779572442383368],
[0.03487645189157884, 0.2010867894533448],
[0.058897267747283544, 0.261442633677628],
[0.11094236876797703, 0.32109432638596125],
[0.18357674052213158, 0.366461802627881],
[0.2453445527225151, 0.38577567277965163],
[0.3414278161453339, 0.39449373916760355],
[0.46095997123681687, 0.3974444693296797],
[0.5793482779542185, 0.38054483294688035],
[0.680006934873362, 0.3668641749227094],
[0.7526413066275168, 0.35760961214165266],
[0.8856136801144534, 0.33407083289418216],
[0.939660515789789, 0.3298459237984823],
[1.1464111094049616, 0.28699327439924127],
[1.2224198338626557, 0.2728700068507589],
[1.3004629743571083, 0.25707402019091785],
[1.393997089974832, 0.23858788733136593],
[1.4895656216293145, 0.21637693665682978],
[1.5784998327141255, 0.2014891617481731],
[1.6547945192653404, 0.18450905090640823],
[1.714045865042745, 0.17292072881534581],
[1.8243128483041704, 0.1492612378794267],
[1.906669931238015, 0.12946452097386185],
[1.9862817780740651, 0.11256488459106251],
[2.1043269302792424, 0.08890539365514338],
[2.18531139516419, 0.07031579363406415],
[2.2999250022471234, 0.0476219962057336],
[2.3854848606283956, 0.02806670267706579],
[2.4495403695769413, 0.00875283252529524],
]
)*1.6

from scipy.interpolate import interp1d


class BUDDIMotor(Motor):
    def __init__(self):
        self.interpolator = interp1d(data[:,0], data[:, 1])
    
    def efficiency(self, torque):
        return self.interpolator(torque)
    #
    #def efficiency(self, torque):
    #    return 0.65-0.125*(torque-0.25)**2

    def calculate(self, rpm, torque):
        return 2 * np.pi * torque * (rpm / 60) / self.efficiency(torque)