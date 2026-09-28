from dataclasses import replace
from pathlib import Path

import geometry as g
import numpy as np
import pandas as pd

from acdesign.aircraft import Wings
from acdesign.aircraft.aircraft import Aircraft
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import ControlSurface, WingPanel
from acdesign.airfoils import Airfoil
from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import FuseAero
from acdesign.performance.propeller import EmpiricalPropeller
from acdesign.performance.propulsion import FactorMotor, PropulsionSystem
from acdesign.solar_wing import SolarWing

avl_workspace = Path("examples/solar_plane/mace2/avl_workspace")
avl_workspace.mkdir(parents=True, exist_ok=True)
wing_airfoil = Airfoil.local("SG6041")
tail_airfoil = Airfoil.local("SD8020")

main_wing = SolarWing.double_taper(
    name="main_wing",
    nrows1=16,
    nrows2=18,
    ncolsroot=3,
    ncolstip=2,
    airfoil=wing_airfoil,
    flap_w=0.1,
    aileron_w=0.1,
    gap=0.02,
)


hstab = SolarWing.straight(
    name="hstab", nrows=8, ncols=1, airfoil=tail_airfoil, control_w=0.08, gap=0.02
)

fin = Wing(
    "fin",
    g.PZ(0.4),
    [
        WingPanel.trapz_crct(
            0.4,
            0.2,
            0.2,
            sym=False,
            dihedral=-np.pi / 2,
            airfoils={0: tail_airfoil},
        )
    ],
).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=1.0))
tail = Wings(
    g.P0(),
    [
        replace(hstab.wing, offset=g.PZ(0.4)).set_control(
            ControlSurface("elevator", 0.3, 0.3, sdup=1.0)
        ),
        replace(fin, offset=fin.offset + g.PY(hstab.wing.b / 2)),
        replace(fin, offset=fin.offset + g.PY(-hstab.wing.b / 2)),
    ],
)

aircraft = Aircraft(
    "MACE2",
    [
        Wings(
            g.PX(0.4),
            [
                main_wing.wing,
            ],
        ),
        replace(tail, offset=g.Point(1.9, 0, 0)),
    ],
    [
        FuseAero.raymers_form_factor(length=1.9, diameter=0.1),
        FuseAero.raymers_form_factor(length=1.9, diameter=0.1),
        FuseAero.raymers_form_factor(length=1.1, diameter=0.16),
    ],
    ref_wing=0,
    reference_point=g.PX(0.5),
    mass=g.Mass.point(8.0),
    #          misc     sensors    antenna            # horns etc
    cd0_offset=0.007
    + (0.1 * 0.05 + 0.006 * 0.06 * 2 + 0.002 * 0.0005) / main_wing.wing.S,
    propulsion=PropulsionSystem(
        propeller=EmpiricalPropeller(
            16 * 25.4 / 1000, 10 * 25.4 / 1000, 0.6
        ),  # a 60% efficient 16x10 propeller
        motor=FactorMotor(0.85),
        n=1,
    ),
)
npanels = main_wing.npanels + hstab.npanels
results_file = Path("examples/solar_plane/mace2", "mace2_option1.csv")
if not results_file.exists():
    results = aircraft.airspeed_sweep(
        Atmosphere.alt(6000), 9, 30, 1, 1.0, avl_workspace, "_6000m"
    )
    results.to_csv(results_file, index=False)
else:
    results = pd.read_csv(results_file)

cells=6
capacity=17.4

if __name__ == "__main__":
    from acdesign.solar_wing import assess_solar_performance

    aircraft.plot().show()
    main_wing.plot().show()

    # Battery: 6S 2900 mAh LiPo, 6 in parallel: 17400 mAh, 2196g
    assess_solar_performance(
        results, aircraft, npanels, cell_power=2.5, battery_capacity=capacity, battery_cells=cells
    )
