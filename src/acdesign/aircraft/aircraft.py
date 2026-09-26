from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path

import geometry as g
import numpy as np
import pandas as pd
from loguru import logger

from acdesign.aircraft.wings import Wings
from acdesign.atmosphere import Atmosphere
from acdesign.avl.avl_runner import run_avl
from acdesign.avl.keywords import kwdict
from acdesign.avl.parse_avl_output import parse_strip_force_df, parse_total_forces
from acdesign.performance.aero import FuseAero
from acdesign.performance.propulsion import PropulsionSystem


@dataclass
class Aircraft:
    """An self in AVL sign convention x aft, y right, z up."""

    name: str
    components: list[Wings]
    bodies: list[FuseAero]
    ref_wing: int  # index of component to use for reference area, span, and chord
    reference_point: g.Point
    mass: g.Mass
    propulsion: PropulsionSystem
    cd0_offset: float = 0.0

    def __post_init__(self):
        self.S = self.components[self.ref_wing].S
        self.b = self.components[self.ref_wing].b
        self.C = self.components[self.ref_wing].C
        _controls = {
            p.control.name: "D"
            for c in self.components
            for w in c.wings
            for p in w.panels
            if p.control is not None
        }
        self.controls = {k: f"D{i + 1}" for i, k in enumerate(_controls.keys())}

    def plot(self, npoints: int = 100, shift: g.Point = None, fig=None, mode="lines"):
        import plotly.graph_objects as go

        fig = fig or go.Figure()
        fig = g.Coord.zero().plot(fig=fig, scale=0.2)

        shift = shift or g.P0()
        for component in self.components:
            fig = component.plot(npoints, shift, fig, mode)
        return fig

    def dump_avl(self, atm: Atmosphere, u: float):
        """Only dump for one operating point as the section cl vs alpha and alpha 0 is adjusted for each local re"""
        avl_header = kwdict["HEADER"](
            self.name,
            0,
            0,
            0,
            0,
            self.S,
            self.C,
            self.b,
            self.reference_point.x[0],
            self.reference_point.y[0],
            self.reference_point.z[0],
        )[1:]
        avl_components = list(
            chain(
                *[c.avl_component(i + 1, atm, u) for i, c in enumerate(self.components)]
            )
        )
        return avl_header + avl_components

    def calculate_drag(
        self,
        atm: Atmosphere,
        u: float,
        load_factor: float = 1.0,
        case_name: str | None = None,
        avl_workspace: str | None = None,
    ):
        """
        Calculate the drag of the self at a given airspeed and load factor.
        """
        case_name = case_name or f"u_{int(u):02d}"

        cl = self.mass.m[0] * load_factor / (0.5 * atm.rho * u**2 * self.S)
        logger.info(f"Creating case u={u:.2f} m/s, cl={cl:.2f}")

        Path(avl_workspace, "geom.avl").write_text("\n".join(self.dump_avl(atm, u)))

        logger.info("Running AVL")

        Path(avl_workspace, f"total_forces_{case_name}.out").unlink(missing_ok=True)
        Path(avl_workspace, f"strip_forces_{case_name}.out").unlink(missing_ok=True)
        _avl_output = run_avl(
            [
                "load geom.avl",
                "oper",
                f"a c {cl}",
                "d1 pm 0",
                "d2 ym 0",
                f"N {case_name}",
                "x",
                f"ft total_forces_{case_name}.out",
                f"fs strip_forces_{case_name}.out",
                " ",
                "QUIT",
            ],
            avl_workspace,
        )

        logger.info("Parsing AVL output")

        tfdf = parse_total_forces(Path(avl_workspace, f"total_forces_{case_name}.out"))
        sfdf = parse_strip_force_df(
            Path(avl_workspace, f"strip_forces_{case_name}.out")
        ).loc[:, ["wing", "panel", "Xle", "Yle", "Zle", "Chord", "Area", "cl", "cd"]]
        sfdf = sfdf.assign(re=atm.rho * u * sfdf.Chord / atm.mu)
        sfdf = pd.merge(
            sfdf, self.airfoil_df, how="left", on=["wing", "panel"], validate="m:1"
        )

        logger.info("Calculating 2D airfoil drag")

        df_2d = []
        for name, airfoil in self.airfoils.items():
            _df = sfdf.loc[sfdf.airfoil == name]
            _odf = airfoil.polar.apply(_df.re, _df.cl, "cl", "oto")
            _df = pd.concat([_df, _odf], axis=1)
            df_2d.append(_df)

        df = pd.concat(df_2d, ignore_index=True)
        df = df.assign(Cdtot=df.cd + df.Cd)

        logger.info("Calculating fuselage drag")

        alpha = np.radians(tfdf["Alpha"])
        body_results = []
        for body in self.bodies:
            body_results.append(body(atm, u, alpha).iloc[0])
        body_cd = sum([b.S * b.Cd for b in body_results]) / self.S

        wing_cd = sum(df.Cdtot * df.Area) / self.S

        logger.info("Calculating total drag")

        cd = sum(df.Cdtot * df.Area / self.S) + body_cd + self.cd0_offset
        
        return dict(
            case=case_name,
            u=u,
            cl_req = cl,
            cl=sum(df.cl * df.Area / self.S),
            cd=cd,
            alpha=np.degrees(alpha),
            wing_cd=wing_cd,
            body_cd=body_cd,
            misc_cd=self.cd0_offset,
        )

    def calculate_design_point(
        self,
        atm: Atmosphere,
        u: float,
        load_factor: float = 1.0,
        case_name: str | None = None,
        avl_workspace: str | None = None,
    ):
        drag_df = self.calculate_drag(atm, u, load_factor, case_name, avl_workspace)
        power = self.propulsion(atm, u, 0.5 * atm.rho * u**2 * self.S * drag_df["cd"])
        return dict(**drag_df, power=power)

    def airspeed_sweep(
        self,
        atm: Atmosphere,
        u_min: int,
        u_max: int,
        load_factor: float = 1.0,
        avl_workspace: str | None = None,
        case_name_suffix: str = "",
    ):
        u_min = int(u_min)
        u_max = int(u_max)
        u_range = np.linspace(u_min, u_max, u_max - u_min + 1)
        results = []
        for u in u_range:
            results.append(
                self.calculate_design_point(
                    atm, u, load_factor, f"u_{int(u):02d}{case_name_suffix}", avl_workspace
                )
            )
        return pd.DataFrame(results)

    def all_airfoils(self):
        return {
            a.name
            for c in self.components
            for w in c.wings
            for p in w.panels
            for k, a in p.airfoils.items()
            if a is not None
        }

    def get_wing_by_name(self, name: str):
        for c in self.components:
            for w in c.wings:
                if w.name == name:
                    return w
        raise ValueError(f"Wing {name} not found")

    @cached_property
    def airfoil_df(self):
        return pd.DataFrame(
            [
                [w.name, i, k, a.name]
                for c in self.components
                for w in c.wings
                for i, p in enumerate(w.panels)
                for k, a in p.airfoils.items()
                if a is not None
            ],
            columns=["wing", "panel", "position", "airfoil"],
        ).drop_duplicates()

    @cached_property
    def airfoils(self):
        return {
            a.name: a
            for c in self.components
            for w in c.wings
            for p in w.panels
            for k, a in p.airfoils.items()
            if a is not None
        }
