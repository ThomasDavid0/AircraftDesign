from pathlib import Path
import geometry as g
from loguru import logger
import numpy as np
import pandas as pd

from acdesign import AVL_WORKSPACE
from acdesign.aircraft import Wings
from acdesign.aircraft.aircraft import Aircraft
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import ControlSurface, WingPanel
from acdesign.avl.avl_runner import run_avl
from acdesign.avl.parse_avl_output import (
    parse_total_forces,
)


aircraft = Aircraft(
    "BoxKite",
    [
        Wings(
            g.PX(0.4),
            [
                Wing(
                    "btm_wing",
                    g.Point(0.0, 0, -0.2),
                    [
                        WingPanel.trapz_crct(
                            0.5,
                            0.3,
                            0.3,
                            control=ControlSurface("flap", 0.3, 0.3, sdup=1.0),
                        ),
                        WingPanel.trapz_crct(
                            1.5,
                            0.3,
                            0.15,
                            control=ControlSurface("aileron", 0.3, 0.4, sdup=-1.0),
                        ),
                    ],
                ),
                Wing(
                    "top_wing",
                    g.Point(0.0, 0, 0.2),
                    [
                        WingPanel.trapz_crct(
                            0.5,
                            0.3,
                            0.3,
                            control=ControlSurface("flap", 0.3, 0.3, sdup=1.0),
                        ),
                        WingPanel.trapz_crct(
                            1.5,
                            0.3,
                            0.15,
                            control=ControlSurface("aileron", 0.3, 0.4, sdup=-1.0),
                        ),
                    ],
                ),
                Wing(
                    "right_wing",
                    g.Point(0.0, 0.25, 0.4),
                    [
                        WingPanel.trapz_crct(
                            0.2, 0.25, 0.35, dihedral=np.radians(-90), sym=False
                        ),
                        WingPanel.trapz_crct(
                            0.4, 0.35, 0.35, dihedral=np.radians(-90), sym=False
                        ),
                        WingPanel.trapz_crct(
                            0.2, 0.35, 0.25, dihedral=np.radians(-90), sym=False
                        ),
                    ],
                ).set_control(ControlSurface("sflap", 0.3, 0.3)),
                Wing(
                    "left_wing",
                    g.Point(0.0, -0.25, 0.4),
                    [
                        WingPanel.trapz_crct(
                            0.2, 0.25, 0.35, dihedral=np.radians(-90), sym=False
                        ),
                        WingPanel.trapz_crct(
                            0.4, 0.35, 0.35, dihedral=np.radians(-90), sym=False
                        ),
                        WingPanel.trapz_crct(
                            0.2, 0.35, 0.25, dihedral=np.radians(-90), sym=False
                        ),
                    ],
                ).set_control(ControlSurface("sflap", 0.3, 0.3)),
            ],
        ),
        Wings(
            g.PX(1.8),
            [
                Wing(
                    "btm_tail",
                    g.Point(0, 0, -0.25),
                    [WingPanel.trapz_crct(0.5, 0.2, 0.2)],
                ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
                Wing(
                    "top_tail",
                    g.Point(0, 0, 0.25),
                    [WingPanel.trapz_crct(0.5, 0.2, 0.2)],
                ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
                Wing(
                    "right_fin",
                    g.Point(0, 0.25, 0.25),
                    [
                        WingPanel.trapz_crct(
                            0.5, 0.2, 0.2, dihedral=np.radians(-90), sym=False
                        )
                    ],
                ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=-1.0)),
                Wing(
                    "left_fin",
                    g.Point(0, -0.25, 0.25),
                    [
                        WingPanel.trapz_crct(
                            0.5, 0.2, 0.2, dihedral=np.radians(-90), sym=False
                        )
                    ],
                ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=-1.0)),
            ],
        ),
    ],
    ref_wing=0,
    reference_point=g.PX(0.5),
    mass=g.Mass.point(5.0),
)

# aircraft.plot().show()

Path(AVL_WORKSPACE, "geom.avl").write_text("\n".join(aircraft.dump_avl()))


#  A lpha        ->  alpha       =   0.000
#  B eta         ->  beta        =   0.000
#  R oll  rate   ->  pb/2V       =   0.000
#  P itch rate   ->  qc/2V       =   0.000
#  Y aw   rate   ->  rb/2V       =   0.000
#  D1  flap      ->  flap        =   0.000
#  D2  aileron   ->  aileron     =   0.000
#  D3  sflap     ->  sflap       =   0.000
#  D4  elevator  ->  elevator    =   0.000
#  D5  rudder    ->  rudder      =   0.000


def setup_flapped_case(name: str, cl: float, cy: float):
    return [
        "a a 0",
        "b b 0",
        f"d1 c {cl}", 
        f"d3 s {cy}", 
        "d4 pm 0", 
        "d5 ym 0", 
        "d2 rm 0", 
        f"N {name}"]


def setup_unflapped_case(name: str, cl: float, cy: float):
    return [
        f"a c {cl}",
        f"b s {cy}",
        "d1 d1 0", 
        "d3 d3 0", 
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
flapped_cases = {}
unflapped_cases = {}
for i, roll_angle in enumerate(np.linspace(0, np.pi, 11)):
    case_name = f"flapped_{np.degrees(roll_angle):.0f}"
    logger.info(f"Running AVL case: {case_name}")
    output += setup_flapped_case(
        case_name, np.cos(roll_angle) * Cly, np.sin(roll_angle) * Cly
    )
    output += run_case(case_name)
    flapped_cases[case_name] = (Cly, roll_angle)

    case_name = f"unflapped_{np.degrees(roll_angle):.0f}"
    logger.info(f"Running AVL case: {case_name}")
    output += setup_unflapped_case(
        case_name, np.cos(roll_angle) * Cly, np.sin(roll_angle) * Cly
    )
    output += run_case(case_name)
    unflapped_cases[case_name] = (Cly, roll_angle)



output += [" "]
output += ["QUIT"]
logger.info("\n".join(output))
run_avl(output)

flapped_results = dict()
for case, (cly, roll_angle) in flapped_cases.items():
    flapped_results[case] = dict(
        roll_angle=roll_angle,
        **parse_total_forces(Path(AVL_WORKSPACE, f"total_forces_{case}.out")),
    )
unflapped_results = dict()
for case, (cly, roll_angle) in unflapped_cases.items():
    unflapped_results[case] = dict(
        roll_angle=roll_angle,
        **parse_total_forces(Path(AVL_WORKSPACE, f"total_forces_{case}.out")),
    )


pd.DataFrame(flapped_results).to_csv(Path("examples/f3a/f3a_avl_flapped_results.csv"))
pd.DataFrame(unflapped_results).to_csv(Path("examples/f3a/f3a_avl_unflapped_results.csv"))
