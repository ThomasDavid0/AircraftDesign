from acdesign.atmosphere import Atmosphere
from dataclasses import dataclass


@dataclass
class OperatingPoint:
    atm: Atmosphere
    V: float

    @property
    def Q(self):
        return 0.5 * self.atm.rho * self.V**2
    
    def to_dict(self):
        return dict(
            rho=self.atm.rho, 
            v = self.V,
            q = self.Q
        )