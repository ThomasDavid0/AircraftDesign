from .keywords import AVLParam, kwdict

from acdesign.aircraft import Rib, Panel, Plane
from typing import NamedTuple, List

from geometry import Point


def rib_dump_avl_tuples(rib: Rib) -> List[NamedTuple]:
    return kwdict["SECTION"].dump(kwdict["SECTION"].create(
            rib.transform.translation.x,
            rib.transform.translation.y,
            rib.transform.translation.z, 
            rib.chord
        )) # + consider adding airfoil stuff here



def panel_dump_avl_tuples(panel: Panel) -> List[NamedTuple]:
    return kwdict["SURFACE"].dump(kwdict["SURFACE"].create(12, 1)) \
        + rib_dump_avl_tuples(
            panel.inbd.offset(Point(-panel.x, -panel.y, panel.z))
        ) \
        + rib_dump_avl_tuples(
            panel.otbd.offset(Point(-panel.x, -panel.y, panel.z))
        )


def plane_dump_avl_tuples(plane: Plane) -> List[NamedTuple]:
    plane = kwdict["HEADER"].dump(kwdict["HEADER"].create(
            plane.name,
            0,
            1, 0, 0, 
            plane.sref, plane.cref, plane.bref, 
            0, 0, 0
        ))[1:] \
        
    for p in plane.panels:
        plane += panel_dump_avl_tuples(p)
    return plane