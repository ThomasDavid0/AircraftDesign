from unittest import result
import numpy as np
import numpy.typing as npt
import pandas as pd
import xarray as xr

from acdesign.atmosphere import Atmosphere
from .operating_point import OperatingPoint
from acdesign.airfoils.polar import UIUCPolar
from typing import Callable, Literal
from scipy.optimize import minimize, Bounds
from acdesign.old_aircraft import Wing
from dataclasses import dataclass


@dataclass
class FuseAero:
    length: float
    diameter: float

    def __call__(self, atm: Atmosphere, v: npt.ArrayLike):
        re = atm.rho * v * self.length / atm.mu
        results = pd.DataFrame().assign(
            fs_v=np.atleast_1d(v),
            re=re,
            S=self.length * np.pi * self.diameter,
            c=self.length,
            Cl=0,
            Cd0=0.455 / (np.log10(re) ** 2.58),
            Cd=0.455 / (np.log10(re) ** 2.58),
            Cm=0,
        )
        return results.assign(
            lift=0,
            drag=0.5 * atm.rho * results.fs_v**2 * results.S * results.Cd,
            moment=0,
        )


@dataclass
class WingIncrement:
    C: float  # chord
    b: float  # span
    x: float  # x location
    y: float  # spanwise location
    polar: UIUCPolar

    @property
    def S(self):
        return self.b * self.C

    def __call__(self, atm: Atmosphere, v: npt.ArrayLike, lift: float):
        q = 0.5 * atm.rho * v**2
        re = atm.rho * v * self.C / atm.mu
        cl = lift / (q * self.S)
        polars = self.polar.lookup(re, cl, "cl")
        return polars.assign(
            re=re,
            drag=q * self.S * polars.Cd,
            moment=lift * self.x + q * self.S * self.C * polars.Cm,
        )


# New wing aero
# wing made up of number of wingincrements , each one has a chord and a polar
# assume the spanwise load distribution,
# run all the polars
# sum the forces


@dataclass
class WingAero:
    b: float
    S: float
    polars: list[UIUCPolar]
    rib_locs: list[float]
    spanchord: Callable[[npt.ArrayLike], npt.ArrayLike] = lambda yb: np.ones_like(
        yb
    )  # spanwise chord distribution

    @property
    def smc(self):
        return self.S / self.b

    @property
    def AR(self):
        return self.b / self.smc

    def stall(self, op: OperatingPoint, spanload=lambda yb: np.sqrt(1 - yb**2)):
        """get the minimum Cl at which any section stalls"""
        re = op.atm.rho * op.V * self.smc / op.atm.mu

        loads = spanload(np.array(self.rib_locs[:-1]))
        clmax = pd.DataFrame([polar.stall(re).iloc[0] for polar in self.polars])

        rib_stall_ratio = clmax.cl / loads
        critical_rib = rib_stall_ratio.to_numpy().argmin()

        local_stall = clmax.iloc[critical_rib]

        stall_cl = local_stall.cl / loads[critical_rib]

        return self(op, stall_cl, spanload)

    def get_cl(self, atm: Atmosphere, v: float, lift: float):
        return 2 * lift / (atm.rho * v**2 * self.S)

    def get_lift(self, atm: Atmosphere, v: float, cl: float):
        return 0.5 * atm.rho * v**2 * self.S * cl

    def __call__(
        self,
        atm: Atmosphere,
        v: npt.ArrayLike,
        lift: npt.ArrayLike,
        spanload=lambda yb: np.sqrt(1 - yb**2),  # spanwise lift distribution
        spanvel=lambda yb: np.ones_like(yb),  # spanwise velocity distribution
        n=50,
        invert=False,
        e: float | Literal["howe"] = 1,  # spanloading efficiency
        mode: Literal["grid", "oto"] = "grid",
    ) -> pd.DataFrame:
        """
        This will calculate a result for every v, l pair
        """
        v = np.atleast_1d(v)
        lift = np.atleast_1d(lift)
        assert v.ndim == 1 and lift.ndim == 1
        if mode == "oto":
            assert v.shape == lift.shape 
        else:
            v, lift = np.meshgrid(v, lift)
            v, lift = v.flatten(), lift.flatten()

        fac = -1 if invert else 1

        ylocs = np.linspace(0, 1, n+1)[:-1] + 0.5/n

        sload = spanload(ylocs)
        sload = sload / np.mean(sload)
        schord = self.spanchord(ylocs)
        schord = schord / np.mean(schord)
        svel = spanvel(ylocs)
        svel = svel / np.mean(svel)

        sprops = pd.DataFrame(dict(yloc=ylocs, sload=sload, schord=schord, svel=svel))

        local_lift = (
            xr.DataArray(
                np.outer(fac * lift, sload / n),
                dims=["wing_l", "yloc"],
                coords={"wing_l": lift, "yloc": ylocs},
            )
            .to_dataframe(name="local_lift")
            .reset_index()
        )

        local_v = (
            xr.DataArray(
                np.outer(v, svel),
                dims=["fs_v", "yloc"],
                coords={"fs_v": v, "yloc": ylocs},
            )
            .to_dataframe(name="v")
            .reset_index()
        )

        _idf = pd.concat([local_lift, local_v.drop(columns="yloc")], axis=1)
        _idf = _idf.merge(sprops, on="yloc")
        _idf = _idf.assign(
            local_cl=2
            * _idf.local_lift * n
            / (atm.rho * _idf.v**2 * self.S * _idf.schord),
            re=atm.rho * _idf.v * self.smc * _idf.schord / atm.mu,
        )

        panel_results = []

        for i, p in enumerate(self.polars):
            _pdf = _idf.loc[
                (_idf.yloc >= self.rib_locs[i]) & (_idf.yloc < self.rib_locs[i + 1])
            ]

            _pdf = _pdf.assign(
                cd0=p.cl_to_cd.oto(_pdf.re, _pdf.local_cl),
                cm=p.cl_to_cm.oto(_pdf.re, _pdf.local_cl),
            )

            _pdf = _pdf.assign(
                gcl=_pdf.svel**2 * _pdf.schord * _pdf.local_cl,
                gcd0=_pdf.svel**2 * _pdf.schord * _pdf.cd0,
                gcm=_pdf.svel**2 * _pdf.schord**2 * _pdf.cm,
            )

            panel_results.append(_pdf)

        k = 1 / (np.pi * (WingAero.e_howe() if e == "howe" else e) * self.AR)

        results = (pd.concat(panel_results)
                   .rename(columns=dict(gcl="Cl", gcd0="Cd0", gcm="Cm"))
                   .loc[:, ["wing_l", "fs_v", "Cl", "Cd0", "Cm"]]
                   .groupby(["wing_l", "fs_v"]))

        results = results.mean().reset_index()

        results = results.assign(
            k=k,
            Cl=results.Cl * fac,
            Cm=results.Cm * fac,
            Cd=results.Cd0 + k * results.Cl**2,
        )

        return results.assign(
            lift=0.5 * atm.rho * results.fs_v**2 * self.S * results.Cl,
            drag=0.5 * atm.rho * results.fs_v**2 * self.S * results.Cd,
            moment=0.5 * atm.rho * results.fs_v**2 * self.S * self.smc * results.Cm,
        )

    def minimize(self, fun: Callable[[pd.Series], float], atm: Atmosphere, lift: npt.ArrayLike, bounds=(5,30), tol=0.1, n=10):
        """get the velocity for minimum drag at a given lift"""
        lift = np.atleast_1d(lift)
        if len(lift) > 1:
            return pd.concat(
                [self.minimize(fun, atm, l, bounds, tol, n) for l in lift], axis=1
            ).T

        step = bounds[1] - bounds[0]
        while step > tol:
            res = self(atm, np.linspace(bounds[0], bounds[1], n), lift, mode="grid")
            
            _res = res.apply(fun, axis=1)
            idx = _res.idxmin()
            bounds = (res.fs_v[max(idx-1, 0)], res.fs_v[min(idx+1, len(res)-1)])
            step = bounds[1] - bounds[0]
        return res.assign(minVal= _res).iloc[idx]
       

    @staticmethod
    def e_howe(
        M,  # mach number
        lam,  # taper ratio
        sw,  # 1/4 chord sweep, radians
        Ne,  # number of engines on the wing
        toc,  # thickness to chord ratio
        A,  # effective aspect ratio
    ):
        """calculation of oswald efficiency factor according to Howe 2000,
        ref https://www.fzt.haw-hamburg.de/pers/Scholz/HOOU/AircraftDesign_13_Drag.pdf
        """

        def f(lam):
            return 0.005 * (1 + 1.5 * (lam - 0.6) ** 2)

        _a = 1 + 0.12 * M**6
        _b = (0.142 + f(lam) * A * (10 * toc) * 0.33) / np.cos(sw) * 2
        _c = 0.1 * (3 * Ne + 1) / (4 + A) ** 0.8
        return 1 / (_a * (1 + _b + _c))


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
            assert v.shape == lift.shape & v.ndim == 1
        else:
            v, lift = np.meshgrid(v, lift)
            v, lift = v.flatten(), lift.flatten()

        _cls = 2 * lift / (atm.rho * v**2 * self.wing.S)
        wing_cl_range = np.linspace(0.8 * min(_cls), 1.5 * max(_cls), npoints)

        wing_l_range = np.linspace(0.8 * min(lift), 1.5 * max(lift), npoints)

        wing = self.wing(
            atm,
            vs,
            ls,
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
        tail = self.tail(op, tail_cl, invert=True)

        tail_force = op.Q * tail["S"] * tail_cl
        tail_moment = op.Q * tail["S"] * tail["Cm"] * tail["c"]

        wing_cl = (lift - tail_force) / (op.Q * self.wing.S)
        wing_coeffs = self.wing(op, wing_cl)
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
            dict(
                wing=self.wing(op, wingcl),
                tail=self.tail(op, tclreq, invert=True),
                fin=self.fin(op, 0),
                fuse=self.fus(op),
            )
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

        df = pd.DataFrame(
            dict(
                wing=self.wing(op, wingcl),
                tail=self.tail(op, tailcl, invert=True),
                fin=self.fin(op, 0),
                fuse=self.fus(op),
            )
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
