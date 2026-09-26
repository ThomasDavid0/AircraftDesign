from pathlib import Path

import numpy as np
import pandas as pd
from mace0 import aircraft, avl_workspace, tail_airfoil, wing_airfoil

from acdesign.atmosphere import Atmosphere
from acdesign.avl.parse_avl_output import parse_total_forces
from acdesign.performance.aero import FuseAero

airfoils = {
    wing_airfoil.name: wing_airfoil,
    tail_airfoil.name: tail_airfoil,
}

pod = FuseAero.raymers_form_factor(length=0.8, diameter=0.16)
pylon = FuseAero.raymers_form_factor(length=1.6, diameter=0.06)
aoa_pole = FuseAero.raymers_form_factor(
    length=0.8, diameter=0.01, setting_angle=np.radians(0)
)

results = []
for u in np.linspace(9, 21, 13):
    atm = Atmosphere.alt(0)

    forces = parse_total_forces(Path(avl_workspace, f"total_forces_u_{int(u):02d}.out"))

    sfdf = pd.read_csv(Path(avl_workspace, f"strip_forces_u_{int(u):02d}.csv"))
    sfdf = sfdf.loc[
        :, ["wing", "panel", "Xle", "Yle", "Zle", "Chord", "Area", "cl", "cd"]
    ]
    sfdf = pd.merge(
        sfdf, aircraft.airfoil_df, how="left", on=["wing", "panel"], validate="m:1"
    )
    sfdf = sfdf.assign(re=atm.rho * u * sfdf.Chord / atm.mu)

    df_2d = []

    for name, airfoil in airfoils.items():
        _df = sfdf.loc[sfdf.airfoil == name]
        _odf = airfoil.polar.apply(_df.re, _df.cl, "cl", "oto")
        _df = pd.concat([_df, _odf], axis=1)
        df_2d.append(_df)

    df = pd.concat(df_2d, ignore_index=True)
    df = df.assign(Cdtot=df.cd + df.Cd)

    alpha = np.radians(forces["Alpha"])
    pod_results = pod(atm, u, alpha).iloc[0]
    pylon_results = pylon(atm, u, alpha).iloc[0]
    aoa_pole_results = aoa_pole(atm, u, alpha).iloc[0]

    wing_cd = sum(df.Cdtot * df.Area) / aircraft.S
     

    cd = (
        sum(df.Cdtot * df.Area / aircraft.S)
        + (
            pod_results.Cd * pod_results.S
            + 2 * pylon_results.Cd * pylon_results.S
            + aoa_pole_results.Cd * aoa_pole_results.S
            + 0.006*0.06*2 # antennas
            + 0.002*0.0005 # aoa sensor
        )
        / aircraft.S
    )
    cl = sum(df.cl * df.Area / aircraft.S)

    print(f"u={u:.2f} m/s, cl={cl:.4f}, cd={cd:.4f}, L/D={cl / cd:.2f}, alpha={np.degrees(alpha):.2f} deg")

    results.append({"u": u, "cl": cl, "cd": cd, "L/D": cl / cd, "alpha": np.degrees(alpha)})

pd.DataFrame(results).to_csv(
    Path("examples/solar_plane/mace0", "l_over_d.csv"), index=False
)
