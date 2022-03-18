from .aero import AeroModel
from .motor import Propulsion



def estimate_mass(aero: AeroModel, batt: Propulsion):
    masses = dict(
        axi_8118 = 3 * 540,
        speed_cont=3*100,
        props = 3*100,
        servos = 5 * 23,
        autopilot = 100,
        cables = 100,
        payload=1000,
        tilt_mechanism = 3*150,
        structure = (1 + 0.2 * aero.b**2 + aero.AR / 5) * 1000,
        battery = (batt.Ah * batt.v0 * 0.00392) * 1000,
    )


    return sum(list(masses.values())) / 1000