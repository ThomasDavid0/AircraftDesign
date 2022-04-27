from os import name
from geometry import Point, Transformation, Mass
import numpy as np
from typing import List, Dict




class ComponentMass:
    def __init__(self, name: str, cg : Point, mass: Mass):
        self.name = name
        self.cg = cg
        self.mass = mass


    @staticmethod
    def combine(components: list):
        cgs = Point.concatenate([c.cg for c in components]) 
        ms = np.array([c.mass.m[0] for c in components])
        
        cg = np.sum(cgs * ms) / np.sum(ms) 

        total = sum(c.mass.offset(c.cg - cg) for c in components)
        
        return ComponentMass("Total",cg,total)

    @staticmethod
    def create(
        name:str, 
        cg: Dict[str, float], 
        m: float,
        geom: dict 
    ):

        shape = geom.pop("shape")
        if shape == "cuboid":
            mass = Mass.cuboid(m, **geom)
        elif shape == "sphere":
            mass = Mass.sphere(m, **geom)
        elif shape == "point":
            mass = Mass.point(m)
        else:
            raise ValueError("unknown mass shape")
        
        return ComponentMass(name, Point(**cg), mass)

    def dumpd(self):
        return dict(
            name=self.name,
            cg=self.cg.to_dict(),
            m=self.mass.m[0],
            geom={"shape": "point"}
        )