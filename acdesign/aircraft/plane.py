from geometry import Point, Transformation
from typing import List
from .panel import Panel



class Plane:
    """An aircraft. Origin on nose, x axis forward, y axis to right, z axis down.
    """
    def __init__(self, panels: List[Panel], bodies:list):
        self.panels = panels
        self.bodies = bodies


    