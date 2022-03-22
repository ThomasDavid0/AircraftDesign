from .keywords import AVLParam, kwdict

from acdesign.aircraft import Rib, Panel, Plane
from typing import NamedTuple, List

from geometry import Point
import numpy as np


def rib_dump_avl(rib: Rib) -> List[NamedTuple]:
    return kwdict["SECTION"].dump(kwdict["SECTION"].create(
            rib.transform.translation.x[0],
            rib.transform.translation.y[0],
            rib.transform.translation.z[0], 
            rib.chord,
            np.degrees(rib.incidence)
        )) # + consider adding airfoil stuff here



def panel_dump_avl(panel: Panel) -> List[NamedTuple]:
    #AVL works in x aft, yright, z up, everythin global, so some conversions done here.
    return kwdict["SURFACE"].dump(kwdict["SURFACE"].create(panel.name, 12, 1)) \
        + rib_dump_avl(
            panel.inbd.offset(Point(-panel.x, panel.y, -panel.z))
        ) \
        + rib_dump_avl(
            panel.otbd.offset(Point(-panel.x, panel.y, -panel.z))
        )


def plane_dump_avl(plane: Plane) -> List[NamedTuple]:
    plane = kwdict["HEADER"].dump(kwdict["HEADER"].create(
            plane.name,
            0,
            1, 0, 0, 
            plane.sref, plane.cref, plane.bref, 
            *plane.mass.cg.to_list()
        ))[1:] \
        
    for p in plane.panels:
        plane += panel_dump_avl(p)
    return plane