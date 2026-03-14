from acdesign.old_aircraft.plane import ConventionalPlane
from acdesign.old_aircraft.wing import Wing
from acdesign.old_aircraft.body import Body
from acdesign.old_aircraft.panel import Panel
from acdesign.old_aircraft.rib import Rib
from acdesign.old_aircraft.component_mass import ComponentMass
from geometry import Point, PX, Mass, Transformation, Q0, Euler, PY, PZ
import numpy as np
from acdesign.airfoils.polar import UIUCPolar



cold_draft = ConventionalPlane(
    "ColdDraft",

    Wing.from_panels([
        Panel.simple(
            name="wing", 
            length=(1859.45 - 157)/2, 
            sweep=447.65-148.38, 
            root=Rib.simple("rae101-il", 447.65, 5), 
            tip=Rib.simple("e268-il", 148.38, 5) 
        ).offset(PY(78.5))
    ]).extend_inboard().offset(PX(-320-90)),

    Wing.from_panels([
        Panel.simple(
            name="tail", 
            length=(366.15), 
            sweep=282.95-69.79, 
            root=Rib.simple("stcyr172-il", 282.95, 5), 
            tip=Rib.simple("stcyr172-il", 69.79, 5) 
        ).offset(PY(48.9))
    ]).extend_inboard().offset(PX(-1633.42)),
    Wing.from_ribs([
        Rib.simple("stcyr172-il", 260.07, 5).offset(Point(1710,-200, 0)),
        Rib.simple("stcyr172-il", 350.93, 5).offset(Point(1619.147,-152.183, 0)),
        Rib.simple("stcyr172-il", 453.38, 5).offset(Point(1511.084,147.394, 0)),
        Rib.simple("stcyr172-il", 200.06, 5).offset(Point(1760,350, 0)),
    ], False).apply_transformation(Transformation())



)

fin =  Wing.from_panels([
        Panel.simple(
            name="fin_btm", 
            length=57.21, 
            sweep=-90.86, 
            tip=Rib.simple("stcyr172-il", 350.93, 5), 
            root=Rib.simple("stcyr172-il", 260.07, 5), 
            dihedral=90
        ).offset(Point(-198.916, 0, 200)),
        Panel.simple(
            name="fin_mid", 
            length=57.21, 
            sweep=-90.86, 
            tip=Rib.simple("stcyr172-il", 350.93, 5), 
            root=Rib.simple("stcyr172-il", 260.07, 5), 
            dihedral=90
        ).offset(Point(-108, 0, 152.183)),
        Panel.simple(
            name="fin_top", 
            length=202.29, 
            sweep=248.916, 
            root=Rib.simple("stcyr172-il", 453.38, 5), 
            tip=Rib.simple("stcyr172-il", 200.06, 5),
            dihedral=90
        ).offset(PZ(147.394))
    ], False).offset(PX(-1511.084))