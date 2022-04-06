from acdesign.aircraft import Plane, Panel, Rib
from acdesign.airfoils.airfoil import Airfoil


from acdesign.avl import parse_avl
#
Plane.parse_avl = parse_avl
