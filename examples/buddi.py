from acdesign.aircraft.plane import ConventionalPlane
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.body import Body
from acdesign.aircraft.component_mass import ComponentMass
from geometry import Point, PX, Mass, Transformation, Q0, Euler
import numpy as np

buddi = ConventionalPlane(
    "Buddi",
    Wing.double_taper(
        "wing",
        3500, 
        1e6, 
        0.6,  
        100, 
        ["clarkysm-il","clarkysm-il","clarkysm-il","sa7038-il"], 
        500
    ).apply_transformation(Transformation(PX(-300), Q0())),
    Wing.straight_taper(
        "tail",
        3500/4,
        0.75/3, 
        0.3,
        20,
        ["s9032-il", "s9032-il"]
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),
    Wing.straight_taper(
        "fin",
        3500/10,
        0.75/6,
        0.32,
        30,
        ["s9032-il", "s9032-il"],
        90,
        False
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),
    [Body.create("body")],
    [ComponentMass("total", PX(400), Mass.point(16) )]

)


def np_encoder(object):
    if isinstance(object, np.generic):
        return object.item()

import json


with open("acdesign/data/buddi_test.json", "w") as f:
   json.dump(buddi.dumpd(), f, default=np_encoder, indent=2)
    
pass