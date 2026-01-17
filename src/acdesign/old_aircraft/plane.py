from geometry import Point, Transformation, Mass
from typing import List
from .panel import Panel
from .body import Body
from .component_mass import ComponentMass
from .wing import Wing
import numpy as np
from json import load, dump, loads, dumps



class Plane:
    """An aircraft. Origin on nose, x axis forward, y axis to right, z axis down.
    """
    def __init__(self, name: str, panels: List[Panel], bodies:List[Body], masses: List[ComponentMass]):
        self.name = name
        self.panels = panels
        self.bodies = bodies
        self.masses = masses
        [m.mass for m in masses]
        self.mass = ComponentMass.combine(masses)

    @staticmethod
    def create(name, panels, bodies=[], masses=[], version=0.01):
        assert version==0.01
        return Plane(
            name,
            [Panel.create(**dat) for dat in panels],
            [Body.create(**dat) for dat in bodies],
            [ComponentMass.create(**mass) for mass in masses]
        )

    def dumpd(self):
        return dict(
            version=0.01,
            name=self.name,
            panels=[p.dumpd() for p in self.panels],
            bodies=[b.dumpd() for b in self.bodies], 
            masses=[m.dumpd() for m in self.masses],
        )

    def dump_json(self, file):
        def np_encoder(object):
            if isinstance(object, np.generic):
                return object.item()
        with open(file, 'w') as f:
            #this is a nice bodge from stack overflow to format floats in json dump
            dump(
                loads(
                    dumps(self.dumpd(), default=np_encoder), 
                    parse_float=lambda x: round(float(x), 3)
                ),
                f, indent=2
            )


    @property
    def sref(self) -> float:
        return sum([p.area for p in self.panels if "wing" in p.name])

    @property
    def cref(self) -> float:
        return max([p.SMC for p in self.panels])

    @property
    def bref(self) -> float:
        return max([p.ymax for p in self.panels]) * 2

    def scale(self, fac: float):
        return Plane(
            self.name, 
            [p.scale(fac) for p in self.panels],
            [b.scale(fac) for b in self.bodies],
            self.masses,
        )

class ConventionalPlane(Plane):
    def __init__(self, name, wing: Wing, tail: Wing, fin: Wing, bodies: list[Body], masses: list[ComponentMass]):
        self.wing = wing
        self.tail = tail
        self.fin = fin
        super().__init__(
            name, 
            wing.panels + tail.panels + fin.panels, 
            bodies, 
            masses
        )
    
    
    @staticmethod
    def parse_json(file):
        if hasattr(file, 'read'):
            plane = Plane.create(**load(f))
        else:
            with open(file, "r") as f:
                plane = Plane.create(**load(f))
        return ConventionalPlane(
            plane.name,
            Wing([p for p in plane.panels if "wing" in p.name]),
            Wing([p for p in plane.panels if "tail" in p.name]),
            Wing([p for p in plane.panels if "fin" in p.name]),
            plane.bodies, plane.masses
        )

    def scale(self, fac):
        return ConventionalPlane(
            self.name,
            self.wing.scale(fac),
            self.tail.scale(fac),
            self.fin.scale(fac),
            [b.scale(fac) for b in self.bodies],
            self.masses,
        )