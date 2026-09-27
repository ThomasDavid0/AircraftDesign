from dataclasses import replace
from pathlib import Path

import geometry as g
import numpy as np
from scipy.interpolate import make_interp_spline
from scipy.optimize import root_scalar

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

flap_w = 0.1
aileron_w = 0.1
gap = 0.01
elevator_w = 0.08

main_wing = SolarWing.double_taper(
    name="main_wing",
    nrows1=16,
    nrows2=18,
    ncolsroot=3,
    ncolstip=2,
    airfoil=wing_airfoil,
    flap_w=flap_w,
    aileron_w=aileron_w,
    gap=gap,
)


hstab = SolarWing.straight(
    name="hstab", nrows=8, ncols=1, airfoil=tail_airfoil, control_w=elevator_w, gap=gap
)  # 1.8, 0.5, 0.0

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
    cd0_offset=0.007 + (0.006 * 0.06 * 2 + 0.002 * 0.0005) / main_wing.wing.S,
    propulsion=PropulsionSystem(
        propeller=EmpiricalPropeller(
            16 * 25.4 / 1000, 10 * 25.4 / 1000, 0.6
        ),  # a 60% efficient 16x10 propeller
        motor=FactorMotor(0.85),
        n=1,
    ),
)


if __name__ == "__main__":
    run = True

    npanels = main_wing.npanels + hstab.npanels
    print(
        f"Total number of panels: {npanels} (wing: {main_wing.npanels}, hstab: {hstab.npanels})"
    )
    aircraft.plot().update_layout(
        template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), width=800, height=400
    ).show()
    main_wing.plot(
        flap_w=flap_w,
        aileron_w=aileron_w,
        gap=gap,
    ).update_layout(
        template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), width=800, height=300
    ).show()

    max_cl = 0.7
    u_4000_cl06 = (
        2 * aircraft.mass.m[0] * 9.81 / (Atmosphere.alt(4000).rho * aircraft.S * max_cl)
    ) ** 0.5

    if run:
        results = aircraft.airspeed_sweep(
            Atmosphere.alt(6000), 9, 30, 2, 1.0, avl_workspace, "_6000m"
        )
        results.to_csv(
            Path("examples/solar_plane/mace2/airspeed_sweep_6000_flapped.csv"),
            index=False,
        )
        spline = make_interp_spline(results.u, results.power)

        def objective(u):
            return npanels * main_wing.cell_power - spline(u)

        bracket = [12, 30]
        result = root_scalar(objective, bracket=bracket, method="brentq")
        if result.converged:
            print(f"Max solar airspeed at 6000 m: {result.root:.2f} m/s")

        # info on 2000m climb
        climb_energy = (
            results.power.min() - npanels * main_wing.cell_power
        ) * 60 * 15 + 9.81 * aircraft.mass.m[0] * 2000
        climb_capacity = climb_energy / (6 * 4.1 * 3600)  # J / (V * 3600) = Ah; 6S pack: 6 cells × 4.1V = 24.6V
        print(f"Climb Energy (15 minutes): {climb_energy:.0f} J")
        print(f"Climb Capacity (15 minutes): {climb_capacity:.2f} Ah")

    print(f"Landing airspeed & 4000m: {u_4000_cl06:.2f} m/s")
