from acdesign.atmosphere import Atmosphere


class OperatingPoint:
    def __init__(self, atm: Atmosphere, V: float):
        self.atm = atm
        self.V = V

    @property
    def Q(self):
        return 0.5 * self.atm.rho * self.V**2