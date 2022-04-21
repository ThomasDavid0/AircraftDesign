from geometry import Point, Transformation
from typing import List
from .panel import Panel
from .body import Body
from .component_mass import ComponentMass
from .wing import Wing
import numpy as np
from json import load



class Plane:
    """An aircraft. Origin on nose, x axis forward, y axis to right, z axis down.
    """
    def __init__(self, name: str, panels: List[Panel], bodies:List[Body], masses: List[ComponentMass]):
        self.name = name
        self.panels = panels
        self.bodies = bodies
        self.masses = masses
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


    @property
    def sref(self) -> float:
        return sum([p.area for p in self.panels if "wing" in p.name])

    @property
    def cref(self) -> float:
        return max([p.mean_chord for p in self.panels])

    @property
    def bref(self) -> float:
        return max([p.ymax for p in self.panels]) * 2


class ConventionalPlane(Plane):
    def __init__(self, name, wing, tail, fin, bodies, masses):
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
        with open(file, "r") as f:
            plane = Plane.create(**load(f))
        return ConventionalPlane(
            plane.name,
            Wing([p for p in plane.panels if "wing" in p.name]),
            Wing([p for p in plane.panels if "tail" in p.name]),
            Wing([p for p in plane.panels if "fin" in p.name]),
            plane.bodies, plane.masses
        )

    