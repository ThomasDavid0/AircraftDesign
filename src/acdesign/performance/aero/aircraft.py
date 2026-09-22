from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.optimize import Bounds, minimize

from acdesign.atmosphere import Atmosphere

from ..operating_point import OperatingPoint
from .fus import FuseAero
from .wing import WingAero


@dataclass
class AircraftAero:
    wing: WingAero
    tail: WingAero
    fin: WingAero
    fus: FuseAero
    pw: float
    pt: float
    cd0_offset: float = 0

    def trim(
        self,
        atm: Atmosphere,
        v: npt.ArrayLike,
        lift: npt.ArrayLike,
        npoints=100,
        wing_sload=lambda yb: np.sqrt(1 - yb**2),
        wing_svel=lambda yb: np.ones_like(yb),
        tail_sload=lambda yb: np.sqrt(1 - yb**2),
        tail_svel=lambda yb: np.ones_like(yb),
        mode: Literal["grid", "oto"] = "oto",
    ):
        """This trim calculation ignores the local pitching moment of the tail"""
        # run the main wing for a cl range that spans the likely trim cl

        v = np.atleast_1d(v)
        lift = np.atleast_1d(lift)
        if mode == "oto":
            assert v.shape == lift.shape and v.ndim == 1
        else:
            v, lift = np.meshgrid(v, lift)
            v, lift = v.flatten(), lift.flatten()

        wing_l_range = np.linspace(0.8 * min(lift), 1.5 * max(lift), npoints)

        wing = self.wing(
            atm,
            v,
            wing_l_range,
            wing_sload,
            wing_svel,
        ).reset_index()

        # calculate the moment at the cg from the wing
        wing = wing.assign(cg_moment=wing.moment - wing.lift * self.pw)

        # run the tail for the full cl range
        tail = self.tail(
            atm,
            v,
            np.linspace(-1, 0.5, npoints),
            tail_sload,
            tail_svel,
            invert=True,
        ).reset_index()

        # calculate moment at the cg from the tail, multiply it by -1
        tail = tail.assign(cg_moment=tail.lift * self.pt - tail.moment)

        # get the tail coefficients for each cl and v
        totals = pd.merge_asof(
            wing.sort_values("cg_moment"),
            tail.sort_values("cg_moment"),
            on="cg_moment",
            by="fs_v",
            suffixes=["_wing", "_tail"],
            direction="nearest",
        )

        totals = totals.assign(
            lift=totals.lift_wing + totals.lift_tail,
        )

        # now find the closest results to the requested lift for each v
        results = pd.DataFrame(
            [(v, l) for v in np.atleast_1d(v) for l in np.atleast_1d(lift)],
            columns=["fs_v", "in_lift"],
        )
        results = pd.merge_asof(
            results.sort_values("in_lift"),
            totals.sort_values("lift"),
            left_on="in_lift",
            right_on="lift",
            by="fs_v",
            direction="nearest",
        )
        results = results.drop(
            columns=[
                "wing_cl_wing",
                "wing_cl_tail",
                "lift",
                "cg_moment",
                "index_wing",
                "index_tail",
            ],
            errors="ignore",
        )

        # now do the fin and fuselage

        results = results.merge(
            self.fin(atm, v, 0).add_suffix("_fin"),
            left_on="fs_v",
            right_on="fs_v_fin",
        )
        results = results.merge(
            self.fus(atm, v).add_suffix("_fuselage"),
            left_on="fs_v",
            right_on="fs_v_fuselage",
        )

        results = results.assign(
            lift=results.lift_wing + results.lift_tail,
            drag=results.drag_wing
            + results.drag_tail
            + results.drag_fin
            + results.drag_fuselage
            + self.cd0_offset * 0.5 * atm.rho * results.fs_v**2 * self.wing.S,
            moment=0,
        )

        return results

    def get_moment(self, op: OperatingPoint, lift: float, tail_cl: float):
        # tail force +ve up
        tail_lift = self.tail.get_lift(op.atm, op.V, tail_cl)
        tail = self.tail(op.atm, op.V, tail_lift)

        tail_force = op.Q * self.tail.S * tail_cl
        tail_moment = op.Q * self.tail.S * tail["Cm"] * self.tail.smc

        wing_cl = (lift - tail_force) / (op.Q * self.wing.S)

        wing_coeffs = self.wing(op.atm, op.V, lift-tail_force)
        wing_moment = op.Q * self.wing.S * self.wing.smc * wing_coeffs["Cm"]
        return (
            wing_moment
            + tail_moment
            - op.Q * self.wing.S * wing_cl * self.pw
            - tail_force * self.pt
        )

    def quick_trim(self, op: OperatingPoint, lift: float):
        # this is not proper trimming but a guess that should be quicker than trim
        mom = self.get_moment(op, lift, 0.0)
        tfreq = mom / self.pt
        tclreq = tfreq / (op.Q * self.tail.S)
        wingcl = (lift + tfreq) / (op.Q * self.wing.S)

        df = pd.DataFrame(
            {
                "wing": self.wing(op, wingcl),
                "tail": self.tail(op, tclreq, invert=True),
                "fin": self.fin(op, 0),
                "fuse": self.fus(op),
            }
        ).T.assign(p=[self.pw, self.pt, 0, 0])

        return df.assign(
            gCl=df.Cl * df.S / self.wing.S,
            gCd=df.Cd * df.S / self.wing.S,
            gCd0=df.Cd0 * df.S / self.wing.S,
        )

    def get_stall_v(self, atm: Atmosphere, lift: float, n=50):
        pass

    def oldtrim(self, op: OperatingPoint, lift: float):
        # TODO this makes it too slow for geometry optimization
        tailcl = minimize(
            lambda tf: abs(self.get_moment(op, lift, tf)),
            0.0,
            bounds=Bounds(-2, 2),
            method="Nelder-Mead",
        ).x
        tail_force = op.Q * self.tail.S * tailcl
        wingcl = (lift + tail_force) / (op.Q * self.wing.S)
        wing_results = self.wing(op.atm, op.V, lift + tail_force)
        df = pd.DataFrame(
            {
                "wing": wing_results,
                "tail": self.tail(op.atm, op.V, tail_force, invert=True),
                "fin": self.fin(op.atm, op.V, 0),
                "fuse": self.fus(op.atm, op.V, wing_results["Alpha"]),
            }
        ).T.assign(p=[self.pw, self.pt, 0, 0])

        return df.assign(
            gCl=df.Cl * df.S / self.wing.S,
            gCd=df.Cd * df.S / self.wing.S,
            gCd0=df.Cd0 * df.S / self.wing.S,
        )

    def calculate_drag(self, op: OperatingPoint, lift: float, quick_trim: bool = False):
        trim = self.quick_trim(op, lift) if quick_trim else self.trim(op, lift)
        cd = np.sum(trim.gCd)

        return op.Q * self.S * (cd + self.cd0_offset)

    def stall_lift(self, op: OperatingPoint):
        # get Cl at which the main wing stalls

        pass

    def stall_speed(self, atm: Atmosphere, lift: float, n=50):
        v = np.linspace(5, 20)
        res = np.array(
            [self.trim(OperatingPoint(atm, v), lift).wing["stall"] for v in v]
        )
        return v[np.argmin(res)]

    @property
    def CLmax(self):
        return 1.1

    @property
    def S(self):
        return self.wing.S
