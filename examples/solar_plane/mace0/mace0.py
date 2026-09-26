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

avl_workspace = Path("examples/solar_plane/mace0/avl_workspace")

wing_airfoil = Airfoil.local("SG6041")
tail_airfoil = Airfoil.local("SD8020")


main_wing = SolarWing.straight_to_elliptical(19, 18, 2, wing_airfoil)
# 1.8, 0.5, 0.0
tail = Wings(
    g.P0(),
    [
        Wing(
            "hstab",
            g.P0(),
            [
                WingPanel.trapz_crct(
                    0.7, 0.15, 0.1, sym=True, airfoils={0: tail_airfoil}
                )
            ],
        ).set_control(ControlSurface("elevator", 0.3, 0.3, sdup=1.0)),
        Wing(
            "fin",
            g.PZ(0.4),
            [
                WingPanel.trapz_crct(
                    0.4,
                    0.15,
                    0.1,
                    sym=False,
                    dihedral=-np.pi / 2,
                    airfoils={0: tail_airfoil},
                )
            ],
        ).set_control(ControlSurface("rudder", 0.3, 0.3, sdup=1.0)),
    ],
)

aircraft = Aircraft(
    "MACE0",
    [
        Wings(
            g.PX(0.4),
            [
                main_wing.wing,
            ],
        ),
        replace(tail, offset=g.Point(1.8, 0.5, 0)),
        replace(tail, offset=g.Point(1.8, -0.5, 0)),
    ],
    [
        FuseAero.raymers_form_factor(length=0.8, diameter=0.16),
        FuseAero.raymers_form_factor(length=1.6, diameter=0.06),
        FuseAero.raymers_form_factor(length=0.8, diameter=0.01),
    ],
    ref_wing=0,
    reference_point=g.PX(0.5),
    mass=g.Mass.point(4.5),
    cd0_offset=0.007 + (0.006 * 0.06 * 2 + 0.002 * 0.0005) / main_wing.wing.S,
    propulsion=PropulsionSystem(
        propeller=EmpiricalPropeller(
            12 * 25.4 / 1000, 6 * 25.4 / 1000, 0.6
        ),  # a 60% efficient 12x6 propeller
        motor=FactorMotor(0.85),
        n=2,
    ),
)


if __name__ == "__main__":
    results_sl = aircraft.airspeed_sweep(Atmosphere.alt(0), 9, 24, 1.0, avl_workspace, "_sl")
    results_sl.to_csv(Path("examples/solar_plane/mace0/airspeed_sweep_sl.csv"), index=False)
    results_9000 = aircraft.airspeed_sweep(
        Atmosphere.alt(9000), 14, 30, 1.0, avl_workspace, "_9000m"
    )
    results_9000.to_csv(Path("examples/solar_plane/mace0/airspeed_sweep_9000.csv"), index=False)

    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.cl / results_sl.cd,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.cl / results_9000.cd,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig.update_layout(
        template="plotly_white",
        title="MACE0 L/D vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="L/D",
    )
    fig.show()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.power,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.power,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig.add_hline(
        y=main_wing.npanels * main_wing.cell_power,
        line_dash="dot",
        annotation_text="Available Solar Power",
        annotation_position="top left",
    )
    fig.update_layout(
        template="plotly_white",
        title="MACE0 Power vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="Power (W)",
    )
    fig.show()
