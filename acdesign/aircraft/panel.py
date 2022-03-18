from geometry import Point, Transformation, Euler
from typing import List
from .rib import Rib
from typing import List
import numpy as np



class PanelProps:
    def __init__(self, p):
        self.ymax = p.otbd.y + p.y
        self.semispan = p.otbd.y - p.inbd.y
        self.mean_chord = (p.inbd.chord + p.otbd.chord) / 2
        self.area =  self.mean_chord * self.semispan           
        self.taper_ratio = p.otbd.chord / p.inbd.chord
        self.le_sweep_distance= p.otbd.x - p.inbd.x
        self.le_sweep_angle = np.arctan2(
            self.le_sweep_distance,
            self.semispan
        )

        cline = p.transform.rotate(Point.X())
        self.incidence = np.arctan2(cline.z, cline.x) - np.pi

        cline = p.transform.rotate(Point.Y())
        self.dihedral = -np.arctan2(cline.z, cline.y)

    
        t = self.taper_ratio
        cr = p.inbd.chord
        #https://www.fzt.haw-hamburg.de/pers/Scholz/HOOU/AircraftDesign_7_WingDesign.pdf
        self.MAC = (2/3)*cr*(1+t+t**2)/(1+t+t**2)
        yMAC = (1/3) * (1 + 2*t) / (1+t)
    
        self.pMAC = Point(yMAC * self.le_sweep_distance / self.semispan , yMAC, 0) 


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

        self.props = PanelProps(self)


    def __getattr__(self, name):
        if name in self.transform.cols:
            return getattr(self.transform, name)
        elif name in self.props.__dict__:
            return getattr(self.props, name)
        raise AttributeError(f"Attribute {name} not found")
        
    def scale(self, fac: float):
        return Panel(
            self.name, 
            Transformation(self.transform.translation * 2, self.transform.rotation),
            self.symm,
            self.inbd.scale(fac),
            self.otbd.scale(fac)
        )

    @property
    def root(self):
        return self.inbd

    @property
    def tip(self):
        return self.otbd

    @staticmethod
    def create(name, acpos, dihedral, incidence, symm, inbd, otbd, sweep, length):

        return Panel(
            name,
            Transformation.build(
                Point(**acpos),
                Euler(np.radians(dihedral) + np.pi, np.radians(incidence), np.pi)
            ),
            symm,
            Rib.create(**inbd),
            Rib.create(**otbd).offset(Point(sweep, length, 0)),
        )

