from acdesign.aircraft.plane import ConventionalPlane
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.body import Body
from acdesign.aircraft.component_mass import ComponentMass
from geometry import Point, PX, Mass, Transformation, Q0, Euler
import numpy as np
from acdesign.airfoils.polar import UIUCPolars

S = 1e6
b=3600
AR = b**2 / S
tailS = 0.2 * S
tailAR = 4
tailb = np.sqrt(tailS * tailAR)
finAR=4
finS = tailS
finb = np.sqrt(finS * finAR)

clarky = UIUCPolars.local("CLARKYB")
pols = clarky.lookup(150000, 0.58)


buddi = ConventionalPlane(
    "Buddi",

    Wing.double_taper(
        name="wing", b=b, S=S, TR=0.6, le_sweep=100, 
        section=["clarkysm-il","clarkysm-il","clarkysm-il","sa7038-il"], 
        incidence=pols.alpha.item(),
        kink_loc=400, gap=60
    ).apply_transformation(Transformation(PX(-300), Q0())),

    Wing.straight_taper(
        "tail", tailb, tailS, 0.8, 50,
        ["s9032-il", "s9032-il"]
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),

    Wing.straight_taper(
        "fin", finb, finS, 0.8, 50,
        ["s9032-il", "s9032-il"],
        90, False
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),

    [Body.create("body")],
    
    [ComponentMass("total", PX(400), Mass.point(16) )]

)


def np_encoder(object):
    if isinstance(object, np.generic):
        return object.item()

import json



with open("acdesign/data/buddi_test.json", "w") as f:
    #this is a nice bodge from stack overflow to format floats in json dump
    json.dump(
        json.loads(
            json.dumps(buddi.dumpd(), default=np_encoder), 
            parse_float=lambda x: round(float(x), 3)
         ),
         f, indent=2
     )
    
pass