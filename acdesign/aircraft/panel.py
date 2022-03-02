from geometry import Point, Transformation, Euler

from .rib import Rib

import numpy as np

class Panel:
    def __init__(
        self, 
        name: str,
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
        self.name= name
        self.transform = transform
        self.symm = symm
        self.inbd = inbd
        self.otbd = otbd

    def __getattr__(self, name):
        if name in ["x", "y", "z", "rw", "rx", "ry", "rz"]:
            return getattr(self.transform, name)

    @property
    def root(self):
        return self.inbd

    @property
    def tip(self):
        return self.otbd

    @property
    def ymax(self):
        return self.otbd.y + self.y

    @property
    def semispan(self):
        return self.otbd.y - self.inbd.y

    @property
    def mean_chord(self): 
        return (self.inbd.chord + self.otbd.chord) / 2

    @property
    def area(self):
        _area =  self.mean_chord * self.semispan
        return 2 * _area if self.symm else _area
            
    @property
    def taper_ratio(self):
        return self.otbd.chord / self.inbd.chord

    @property
    def le_sweep_distance(self):
        return self.otbd.x - self.inbd.x

    @property
    def le_sweep_angle(self):
        return np.arctan2(
            self.le_sweep_distance,
            self.semispan
        )

    @property
    def incidence(self):
        cline = self.transform.rotate(Point(1,0,0))
        return np.arctan2(cline.z, cline.x) - np.pi

    @staticmethod
    def create(name, acpos, dihedral, incidence, symm, inbd, otbd, sweep, length):

        return Panel(
            name,
            Transformation(
                Point(**acpos),
                Euler(np.radians(dihedral) + np.pi, np.radians(incidence), np.pi)
            ),
            symm,
            Rib.create(**inbd),
            Rib.create(**otbd).offset(Point(sweep, length, 0)),
        )

