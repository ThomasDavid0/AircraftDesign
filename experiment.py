

import freecad
App= freecad.app

import acdesign.cad.geom_to_freecad 
from acdesign.cad.create import create_plane
from acdesign.aircraft import Plane, Panel
import numpy as np
from geometry import Transformation, Point, Quaternion, Euler


from json import load

with open("tests/data/aircraft.json", "r") as f:
    plane = Plane.create(**load(f))


doc = create_plane(plane,"/home/tom/projects/f3a_design/test_plane.FCStd" )
