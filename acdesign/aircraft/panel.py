from geometry import Point, Transformation, Euler, PX, PY
from typing import List
from .rib import Rib
from typing import List
import numpy as np



class PanelProps:
    def __init__(self, p):
        self.ymax = p.otbd.y + p.y
        self.semispan = p.otbd.y[0] - p.inbd.y[0]
        self.mean_chord = (p.inbd.chord + p.otbd.chord) / 2
        self.area =  self.mean_chord * self.semispan           
        self.taper_ratio = p.otbd.chord / p.inbd.chord
        self.le_sweep_distance= p.otbd.x[0] - p.inbd.x[0]
        self.le_sweep_angle = np.arctan2(
            self.le_sweep_distance,
            self.semispan
        )

        cline = p.transform.rotate(PX())
        self.incidence = np.arctan2(cline.z[0], cline.x[0]) - np.pi

        cline = p.transform.rotate(PY())
        self.dihedral = -np.arctan2(cline.z[0], cline.y[0])

    
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
        ribs: List[Rib]
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
        self.ribs = ribs
        self.props = PanelProps(self)

    def __getattr__(self, name):
        if name in ["inbd", "root"]:
            return self.ribs[0]
        elif name in ["otbd", "tip"]:
            return self.ribs[-1]
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
            [r.scale(fac) for r in self.ribs]
        )

    @staticmethod
    def create(name, acpos, dihedral, incidence, symm, inbd, otbd, sweep, length):

        return Panel(
            name,
            Transformation.build(
                Point(**acpos),
                Euler(np.radians(dihedral) + np.pi, np.radians(incidence), np.pi)
            ),
            symm,
            [
                Rib.create(**inbd),
                Rib.create(**otbd).offset(Point(sweep, length, 0)),
            ]
        )

