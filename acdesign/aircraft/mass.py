from geometry import Point, Transformation, Points
import numpy as np
from typing import List, Dict

class Mass:
    def __init__(self, name: str, cg : Point, mass: float, inertia : np.ndarray = np.zeros((3,3))):
        self.name = name
        self.cg = cg
        self.mass = mass
        assert inertia.shape == (3,3)
        self.inertia = inertia


    @staticmethod
    def combine(masses: list):
        total = sum(m.mass for m in masses)
        weighted_masses = [m.cg * m.mass for m in masses]
        tmass = Point.zeros()
        for m in weighted_masses:
            tmass += m
        cg = tmass / total
        return Mass("Total",cg,total)

    @staticmethod
    def create(
        name:str, 
        cg: Dict[str, float], 
        mass: float, 
        inertia: List[List[float]] = [[1,0,0],[0,1,0],[0,0,1]]
    ):
        return Mass(name, Point(**cg), mass, np.array(inertia))