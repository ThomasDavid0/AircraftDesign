

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from acdesign.atmosphere import Atmosphere


@dataclass
class FuseAero:
    length: float
    diameter: float

    def __call__(self, atm: Atmosphere, v: npt.ArrayLike, alpha: npt.ArrayLike = None):

        alpha = alpha or np.zeros_like(np.atleast_1d(v))

        re = atm.rho * v * self.length / atm.mu
        cd0 = 0.455 / (np.log10(re) ** 2.58)
        cd = cd0 + self.length * self.diameter * np.sin(
            np.radians(np.atleast_1d(alpha))
        ) ** 2 / (self.length * np.pi * self.diameter)

        results = pd.DataFrame().assign(
            fs_v=np.atleast_1d(v),
            re=re,
            S=self.length * np.pi * self.diameter,
            c=self.length,
            alpha=np.atleast_1d(alpha),
            Cl=0,
            Cd0=cd0,
            Cd=cd,
            Cm=0,
        )
        return results.assign(
            lift=0,
            drag=0.5 * atm.rho * results.fs_v**2 * results.S * results.Cd,
            moment=0,
        )
