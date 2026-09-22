from pathlib import Path
import geometry as g
from loguru import logger
import numpy as np
import pandas as pd

from dataclasses import replace

from acdesign import AVL_WORKSPACE
from acdesign.aircraft import Wings
from acdesign.aircraft.aircraft import Aircraft
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import ControlSurface, WingPanel
from acdesign.avl.avl_runner import run_avl
from acdesign.avl.parse_avl_output import (
    parse_total_forces,
)

from acdesign.airfoils.polar import UIUCPolar
from acdesign.airfoils.airfoil import Airfoil
from acdesign.solar_wing import SolarWing

section = UIUCPolar.local("SG6041")

main_wing = SolarWing.straight_to_elliptical(19, 18, 2, section).wing
#1.8, 0.5, 0.0
tail = Wings(
            g.P0(),
            [
                Wing(
                    "hstab",
                    g.P0(),
                    [WingPanel.trapz_crct(0.7, 0.15, 0.1, sym=True)],
                ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
                Wing(
                    "fin",
                    g.PZ(0.4),
                    [WingPanel.trapz_crct(0.4, 0.15, 0.1, sym=False, dihedral=-np.pi / 2)],
                ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=1.0)),
            ],
        )

 
aircraft = Aircraft(
    "MACE0",
    [
        Wings(
            g.PX(0.4),
            [
                main_wing,
            ],
        ),
        replace(tail, offset=g.Point(1.8, 0.5, 0))
        ,
        replace(tail, offset=g.Point(1.8, -0.5, 0))
    ],
    ref_wing=0,
    reference_point=g.PX(0.5),
    mass=g.Mass.point(4.5),
)

aircraft.plot().show()

Path(AVL_WORKSPACE, "geom.avl").write_text("\n".join(aircraft.dump_avl()))



def setup_case(name: str, cl: float):
    return [
        f"a c {cl}",
        "d1 m 0", 
        "d4 pm 0", 
        "d5 ym 0", 
        "d2 rm 0", 
        f"N {name}"
    ]


def run_case(name: str):
    return ["x", f"ft total_forces_{name}.out", f"st stability_derivatives{name}.out"]


arspd = 20
g_force = 1.0
roll_angle = 0.0
Cly = g_force * sum(aircraft.mass.m) / (0.5 * 1.225 * arspd**2 * aircraft.S)


output = [
    "load geom.avl",
    "oper",
]
cases = {}
for i, cl in enumerate(np.linspace(0, 1, 11)):
    case_name = f"cl_{np.degrees(roll_angle):.0f}"
    logger.info(f"Running AVL case: {case_name}")
    output += setup_case(
        case_name, cl
    )
    output += run_case(case_name)
    cases[case_name] = (Cly, roll_angle)

output += [" "]
output += ["QUIT"]

logger.info("\n".join(output))
run_avl(output)


