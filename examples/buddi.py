from acdesign.old_aircraft.plane import ConventionalPlane
from acdesign.old_aircraft.wing import Wing
from acdesign.old_aircraft.body import Body
from acdesign.old_aircraft.component_mass import ComponentMass
from geometry import Point, PX, Mass, Transformation, Q0, Euler
import numpy as np
from acdesign.airfoils.polar import UIUCPolar


clarky = UIUCPolar.local("CLARKYB")
pols = clarky.lookup(150000, 0.58)


buddi = ConventionalPlane(
    "Buddi",

    Wing.double_taper(
        name="wing", b=3600, S=1e6, TR=0.6, le_sweep=100, 
        section=["clarkysm-il","clarkysm-il","clarkysm-il","sa7038-il"], 
        incidence=pols.alpha.item(),
        kink_loc=400, gap=60
    ).apply_transformation(Transformation(PX(-300), Q0())).fill_gaps(),

    Wing.straight_taper(
        "tail", np.sqrt(2e5  * 4), 2e5, 0.8, 50,
        ["s9032-il", "s9032-il"]
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),

    Wing.straight_taper(
        "fin", np.sqrt(2e5 * 4), 2e5, 0.8, 50,
        ["s9032-il", "s9032-il"],
        90, False
    ).apply_transformation(Transformation(Point(-1400, 0, 55), Q0())),

    [Body.simple("body", )],
    
    [ComponentMass("total", PX(400), Mass.point(16) )]

)

#buddi.dump_json("acdesign/data/buddi_test2.json")
from acdesign.avl.dump import plane_dump_avl

balt = True
with open("examples/buddi.avl", "w") as f:
    for line in plane_dump_avl(buddi.scale(1/1000), True):
        balt=not balt
        f.write(f"{line}\n")
        if balt:
            f.write("\n")

