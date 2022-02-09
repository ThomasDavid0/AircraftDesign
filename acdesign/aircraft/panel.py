from geometry import Point, Transformation, Euler

from .rib import Rib

import numpy as np

class Panel:
    def __init__(
        self, 
        transform: Transformation, 
        symm: bool,
        inbd: Rib, 
        otbd: Rib
    ):
        """A panel represents a constant taper section of wing, tail, fin etc.  
        right wing is modelled, sym reflects to left wing.

        Args:
            transform (Transformation): from body frame to y axis along length of panel, x axis aft, z up)
            symm (bool): [description]
            inbd (Rib): [description]
            otbd (Rib): [description]
        """
        self.transform = transform
        self.symm = symm
        self.inbd = inbd
        self.otbd = otbd

    @property
    def semispan(self):
        return self.otbd.transform.translation.z - self.inbd.transform.translation.z

    @property
    def mean_chord(self): 
        return self.inbd.chord + self.otbd.chord

    @property
    def area(self):
        _area =  0.5 * self.mean_chord * self.semispan
        return 2 * _area if self.symm else _area
            
    @property
    def taper_ratio(self):
        return self.otbd.chord / self.inbd.chord

    @property
    def le_sweep_distance(self):
        return self.inbd.transform.translation.x - self.otbd.transform.translation.x

    @property
    def le_sweep_angle(self):
        return np.arctan2(
            self.le_sweep_distance,
            self.semispan
        )

    @staticmethod
    def create(
        pos: Point, 
        span :float,
        symm: bool,
        dihedral: float, 
        le_sweep: float,
        root: Rib,
        tip: Rib
    ):

        return Panel(
            Transformation(pos, Euler(dihedral, np.pi, 0)),
            True,
            root,
            tip.offset(Point(le_sweep, span, 0)),
        )