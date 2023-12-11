from .aero import AircraftAero
from .propulsion import Battery



def estimate_mass(aero: AircraftAero, batt: Battery):
    masses = dict(
        axi_8118 = 3 * 540,
        speed_cont=3*100,
        props = 3*100,
        servos = 5 * 23,
        autopilot = 100,
        cables = 100,
        payload=1000,
        tilt_mechanism = 3*150,
        #structure = (2 + 0.35 * aero.wing.b**2) * 1000,
        structure = (1 + 0.3 * aero.wing.b**2 + 0.1*aero.wing.b / aero.wing.smc) * 1000,
        battery = (batt.Ah * batt.v0 * 0.00392) * 1000,
    )


    return sum(list(masses.values())) / 1000
