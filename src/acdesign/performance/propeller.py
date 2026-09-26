from dataclasses import dataclass
from importlib.resources import files
from itertools import product

import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator


def getresource(name: str):
    return files("data") / name


class Propeller:
    def calculate(thrust, airspeed, rho):
        return 3000, thrust * airspeed / (2 * np.pi * 3000 / 60)

    def __call__(self, thrust, airspeed, rho):
        rpm, torque = self.calculate(thrust, airspeed, rho)
        return pd.DataFrame(dict(rpm=rpm, torque=torque))


@dataclass
class EmpiricalPropeller:
    """
    Empirical propeller performance model using geometric metrics.
    
    Attributes:
        diameter (float): Propeller diameter in metres (m).
        pitch (float): Propeller pitch in metres (m).
        baseline_efficiency (float): Expected aerodynamic efficiency (0.0 to 1.0) during cruise.
    """
    diameter: float
    pitch: float
    baseline_efficiency: float = 0.8
    
    def calculate(self, thrust: float, airspeed: float, rho: float) -> dict:
        thrust = np.clip(thrust, 0, None)
        airspeed = np.clip(airspeed, 0, None)

        #https://www.tytorobotics.com/blogs/articles/how-to-calculate-propeller-thrust
        k = (np.pi / 4.0) * rho * (self.diameter ** 2)
        
        a_coeff = k * (self.pitch ** 2)
        b_coeff = -k * self.pitch * airspeed
        c_coeff = -thrust

        # n = (-b + sqrt(b^2 - 4ac)) / 2a
        discriminant = (b_coeff ** 2) - (4 * a_coeff * c_coeff)
        rps = (-b_coeff + np.sqrt(discriminant)) / (2 * a_coeff)
        rpm = rps * 60.0

        # 2. Dynamic power scaling based on airspeed regime
        p_shaft = np.where(
            airspeed < 0.1,
            thrust * (self.pitch * rps) / self.baseline_efficiency,
            (thrust * airspeed) / self.baseline_efficiency,
        )

        omega = 2 * np.pi * rps
        torque = np.where(omega > 0, p_shaft / omega, 0.0)

        return rpm, torque

class ConstantPropeller(Propeller):
    def __init__(self, factor, rpm=2000):
        self.factor = factor
        self.rpm = rpm

    def calculate(self, thrust, airspeed, rho):
        return self.rpm, thrust * airspeed / (self.factor * 2 * np.pi * self.rpm / 60)


class LookupPropeller(Propeller):
    def __init__(self, data: pd.DataFrame):
        self.data = data

        self._pa_to_t = LinearNDInterpolator(
            (self.data.Pin_d_rho, self.data.airspeed), self.data.thrust_d_rho
        )
        self._ra_to_t = LinearNDInterpolator(
            (self.data.rpm, self.data.airspeed), self.data.thrust_d_rho
        )
        self._ra_to_p = LinearNDInterpolator(
            (self.data.rpm, self.data.airspeed), self.data.Pin_d_rho
        )
        self._ta_to_r = LinearNDInterpolator(
            (self.data.thrust_d_rho, self.data.airspeed), self.data.rpm
        )
        self._ta_to_p = LinearNDInterpolator(
            (self.data.thrust_d_rho, self.data.airspeed), self.data.Pin_d_rho
        )

    def pa_to_t(self, Pin, airspeed, rho):
        return self._pa_to_t(Pin / rho, airspeed) * rho

    def ra_to_t(self, rpm, airspeed, rho):
        return self._ra_to_t(rpm, airspeed) * rho

    def ra_to_p(self, rpm, airspeed, rho):
        return self._ra_to_p(rpm, airspeed) * rho

    def ta_to_r(self, thrust, airspeed, rho):
        return self._ta_to_r(thrust / rho, airspeed)

    def ta_to_p(self, thrust, airspeed, rho):
        return self._ta_to_p(thrust / rho, airspeed) * rho

    @staticmethod
    def from_df(diameter: float, data: pd.DataFrame):
        arsps = np.linspace(5, 40, 20)
        rpms = np.linspace(50, 7000, 20)
        dfm = pd.DataFrame(product(*[rpms, arsps]), columns=["rpm", "airspeed"])

        dfm["n"] = dfm.rpm / 60
        dfm["J"] = dfm.airspeed / (dfm.n * diameter)
        dfm["Ct"] = np.interp(dfm.J, data.J, data.Ct)
        dfm["efficiency"] = np.interp(dfm.J, data.J, data.efficiency)
        dfm["thrust_d_rho"] = dfm.Ct * dfm.n**2 * diameter**4
        dfm["Cpow"] = dfm.J * dfm.Ct / dfm.efficiency
        dfm["Pin_d_rho"] = dfm.Cpow * dfm.n**3 * diameter**5

        return LookupPropeller(dfm)

    @staticmethod
    def proprawdata(prop_name):
        return pd.read_csv(files("acdesign") / f"data/propellers/{prop_name}.csv")

    @staticmethod
    def load(diameter: float, prop_name: str):
        return LookupPropeller.from_df(diameter, LookupPropeller.proprawdata(prop_name))

    def calculate(self, thrust, airspeed, rho):
        rpm = self.ta_to_r(thrust, airspeed, rho)
        p = self.ta_to_p(thrust, airspeed, rho)
        return rpm, p / (2 * np.pi * rpm / 60)


if __name__ == "__main__":
    prop = LookupPropeller.load(22 * 25.4 / 1000, "mezjlik_2212")
    print(prop.ta_to_r(20, 20, 1.225))
