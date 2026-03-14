from pathlib import Path

import geometry as g
import numpy as np

from acdesign import AVL_WORKSPACE
from acdesign.aircraft import Wings
from acdesign.aircraft.aircraft import Aircraft
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import ControlSurface, WingPanel
from acdesign.avl.avl_runner import run_avl



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
                        WingPanel.trapz_crct( 0.5, 0.3, 0.3, control=ControlSurface("flap", 0.3, 0.3, sdup=1.0)),
                        WingPanel.trapz_crct( 1.5, 0.3, 0.15, control=ControlSurface("aileron", 0.3, 0.4, sdup=-1.0)),
                    ],
                ),
                Wing(
                    "top_wing",
                    g.Point(0.0, 0, 0.2),
                    [
                        WingPanel.trapz_crct( 0.5, 0.3, 0.3, control=ControlSurface("flap", 0.3, 0.3, sdup=1.0)),
                        WingPanel.trapz_crct( 1.5, 0.3, 0.15, control=ControlSurface("aileron", 0.3, 0.4, sdup=-1.0)),
                    ],
                ),
                Wing(
                    "right_wing",
                    g.Point(0.0, 0.25, 0.4),
                    [
                        WingPanel.trapz_crct(0.2, 0.25, 0.35, dihedral=np.radians(-90), sym=False),
                        WingPanel.trapz_crct(0.4, 0.35, 0.35, dihedral=np.radians(-90), sym=False),
                        WingPanel.trapz_crct(0.2, 0.35, 0.25, dihedral=np.radians(-90), sym=False),
                    ],
                ).set_control(ControlSurface("sflap", 0.3, 0.3)),
                Wing(
                    "left_wing",
                    g.Point(0.0, -0.25, 0.4),
                    [
                        WingPanel.trapz_crct(0.2, 0.25, 0.35, dihedral=np.radians(-90), sym=False),
                        WingPanel.trapz_crct(0.4, 0.35, 0.35, dihedral=np.radians(-90), sym=False),
                        WingPanel.trapz_crct(0.2, 0.35, 0.25, dihedral=np.radians(-90), sym=False),
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
                    [
                        WingPanel.trapz_crct( 0.5, 0.2, 0.2)
                    ],
                ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
                Wing(
                    "top_tail",
                    g.Point(0, 0, 0.25),
                    [
                        WingPanel.trapz_crct( 0.5, 0.2, 0.2)
                    ],
                ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
                Wing(
                    "right_fin",
                    g.Point(0, 0.25, 0.25),
                    [
                        WingPanel.trapz_crct( 0.5, 0.2, 0.2, dihedral=np.radians(-90), sym=False)
                    ],
                ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=-1.0)),
                Wing(
                    "left_fin",
                    g.Point(0, -0.25, 0.25),
                    [
                        WingPanel.trapz_crct( 0.5, 0.2, 0.2, dihedral=np.radians(-90), sym=False)
                    ],
                ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=-1.0))
            ],
        ),
    ],
    ref_wing=0,
    reference_point=g.PX(0.5),
    mass=g.Mass.point(5.0),
)

aircraft.plot().show()

Path(AVL_WORKSPACE, "geom.avl").write_text("\n".join(aircraft.dump_avl()))
#aircraft.dump_avl()
# run_avl(
#    [
#        "load f3a.avl",
#        "OPER",
#        *chain(*[run_cl(i, alpha)  for i, alpha in enumerate(alphas)]),
#        "",
#        "QUIT",
#    ]
# )
