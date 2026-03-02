from dataclasses import dataclass
from pathlib import Path
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import ControlSurface, WingPanel
from acdesign.avl.keywords import kwdict
from acdesign.aircraft.wings import PlacedWing, Wings
import geometry as g
import numpy as np
from acdesign.avl.avl_runner import run_avl
from itertools import chain


wings = Wings([
    PlacedWing(
        [
            WingPanel.trapz_crct(0.6, 0.3, 0.3).add_control(ControlSurface("flap", 0.3, 0.3, sdup=1.0)),
            WingPanel.trapz_crct(1.4, 0.3, 0.15).add_control(ControlSurface("aileron", 0.3, 0.4, sdup=-1.0)),
        ],  
        "btm_wing",
        g.Point(0.25, 0, -0.25),
        np.radians(0)
    ),
    PlacedWing(
        [
            WingPanel.trapz_crct(0.6, 0.3, 0.3).add_control(ControlSurface("flap", 0.3, 0.3, sdup=1.0)),
            WingPanel.trapz_crct(1.4, 0.3, 0.15).add_control(ControlSurface("aileron", 0.3, 0.4, sdup=-1.0)),
        ],  
        "top_wing",
        g.Point(0.25, 0, 0.25),
        np.radians(0)
    ),
    PlacedWing(
        [
            WingPanel.trapz_crct(0.2, 0.25, 0.35),
            WingPanel.trapz_crct(0.4, 0.35, 0.35).add_control(ControlSurface("flap", 0.3, 0.3, sdup=-1.0)),
            WingPanel.trapz_crct(0.2, 0.35, 0.25)
        ],
        "side_wing",
        g.Point(0.25, 0.25, 0.4),
        np.radians(-90),
        symm=False,
    )
])

tails = Wings([
    PlacedWing(
        [WingPanel.trapz_crct(0.5, 0.2, 0.2).add_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0))],
        "btm_tail",
        g.Point(1.8, 0, -0.25),
        np.radians(0)
    ),
        PlacedWing(
        [WingPanel.trapz_crct(0.5, 0.2, 0.2).add_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0))],
        "top_tail",
        g.Point(1.8, 0, 0.25),
        np.radians(0)
    ),
        PlacedWing(
        [WingPanel.trapz_crct(0.5, 0.2, 0.2).add_control(ControlSurface("rudder", 0.3, 0.3, sdup=-1.0))],
        "side_tail",
        g.Point(1.8, 0.25, -0.25),
        np.radians(90),
        symm=False,
    )
])


S = wings.btm_wing.S + wings.top_wing.S
b = wings.btm_wing.b
smc = wings.btm_wing.S / b

    

odata = kwdict["HEADER"](
            "MACE 1", 0, 0, 0, 0, S, smc, b, - 0.25 - smc / 4, 0, 0
        )[1:]
odata += wings.avl_component( component=1)

odata += tails.avl_component( component=2)

Path("avl/f3a.avl").write_text("\n".join(odata))

alphas = np.linspace(-5.0, 5.0, 11)
betas = np.linspace(-5.0, 5.0, 11)

alpha_beta = np.meshgrid(alphas, betas)

def run_cl(name: str, alpha: float):
    return [
        f"a a {alpha}",
        "x",
        f"st total_forces_{name}.out",
        f"fs strip_forces_{name}.out",
    ]


#run_avl(
#    [
#        "load f3a.avl",
#        "OPER",
#        *chain(*[run_cl(i, alpha)  for i, alpha in enumerate(alphas)]),
#        "",
#        "QUIT",
#    ]
#)
