from .aero import AircraftAero
from .motor import Propulsion



def estimate_mass(aero: AircraftAero, batt: Propulsion):
    masses = dict(
        axi_8118 = 3 * 540,
        speed_cont=3*100,
        props = 3*100,
        servos = 5 * 23,
        autopilot = 100,
        cables = 100,
        payload=1000,
        tilt_mechanism = 3*150,
        structure = (1 + 0.2 * aero.wing.b**2 + aero.wing.b / (aero.wing.smc * 3.5)) * 1000,
        battery = (batt.Ah * batt.v0 * 0.00392) * 1000,
    )


    return sum(list(masses.values())) / 1000
