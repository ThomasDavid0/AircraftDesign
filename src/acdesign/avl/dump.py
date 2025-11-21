from .keywords import AVLParam, kwdict

from acdesign.old_aircraft import Rib, Panel, Plane
from typing import NamedTuple, List

from geometry import P0, Transformation, Euler
import numpy as np


def rib_dump_avl(rib: Rib, comms=False) -> List[NamedTuple]:
    return kwdict["SECTION"].dump(kwdict["SECTION"].create(
            rib.transform.translation.x[0],
            rib.transform.translation.y[0],
            rib.transform.translation.z[0], 
            rib.chord,
            np.degrees(rib.incidence)
        ), comms) # + consider adding airfoil stuff here



def panel_dump_avl(panel: Panel, symm=True, comms=False) -> List[NamedTuple]:
    #AVL works in x aft, yright, z up, everythin global, so some conversions done here.
    con = Transformation(P0(), Euler(0, np.pi, 0))
    return kwdict["SURFACE"].dump(kwdict["SURFACE"].create(panel.name, 1, 1.0, 16, -2.0), comms) \
        + rib_dump_avl(
            panel.inbd.apply_transformation(con.apply(panel.transform)), 
            comms
        ) \
        + rib_dump_avl(
            panel.otbd.apply_transformation(con.apply(panel.transform)), #.offset(Point(-panel.x, panel.y, -panel.z)), 
            comms
        )


def plane_dump_avl(plane: Plane, comms=False) -> List[NamedTuple]:
    ptups = kwdict["HEADER"].dump(
        kwdict["HEADER"].create(
            plane.name,
            0,
            1, 0, 0, 
            plane.sref, plane.cref, plane.bref, 
            *plane.mass.cg.data[0]
        ), 
        comms
    )[2 if comms else 1:]
        
    for p in plane.panels:
        ptups += panel_dump_avl(p, False, comms)
    return ptups