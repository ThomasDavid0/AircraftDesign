from geometry import Point, Transformation
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
        cg = sum([m.cg * m.mass for m in masses]) / total
        return Mass("Total",cg,total)

    @staticmethod
    def create(
        name:str, 
        cg: Dict[str, float], 
        mass: float, 
        inertia: List[List[float]] = [[1,0,0],[0,1,0],[0,0,1]]
    ):
        return Mass(name, Point(**cg), mass, np.array(inertia))