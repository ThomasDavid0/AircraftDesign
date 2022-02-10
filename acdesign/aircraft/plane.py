from geometry import Point, Transformation
from typing import List
from .panel import Panel



class Plane:
    """An aircraft. Origin on nose, x axis forward, y axis to right, z axis down.
    """
    def __init__(self, name: str, panels: List[Panel], bodies:list):
        self.name = name
        self.panels = panels
        self.bodies = bodies


    @staticmethod
    def create(name, panels, bodies, version):
        assert version ==0.01
        return Plane(
            name,
            [Panel.create(**dat) for dat in panels],
            []
        )