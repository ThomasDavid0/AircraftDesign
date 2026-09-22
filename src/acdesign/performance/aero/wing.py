from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
import pandas as pd
import xarray as xr

from acdesign.airfoils.polar import UIUCPolar
from acdesign.atmosphere import Atmosphere

from ..operating_point import OperatingPoint


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

        ylocs = np.linspace(0, 1, n + 1)[:-1] + 0.5 / n

        sload = spanload(ylocs)
        sload = sload / np.mean(sload)
        schord = self.spanchord(ylocs)
        schord = schord / np.mean(schord)
        svel = spanvel(ylocs)
        svel = svel / np.mean(svel)

        sprops = pd.DataFrame({"yloc": ylocs, "sload": sload, "schord": schord, "svel": svel})

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
            * _idf.local_lift
            * n
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

        results = (
            pd.concat(panel_results)
            .rename(columns={"gcl": "Cl", "gcd0": "Cd0", "gcm": "Cm"})
            .loc[:, ["wing_l", "fs_v", "Cl", "Cd0", "Cm"]]
            .groupby(["wing_l", "fs_v"])
        )

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

    def minimize(
        self,
        fun: Callable[[pd.Series], float],
        atm: Atmosphere,
        lift: npt.ArrayLike,
        bounds=(5, 30),
        tol=0.1,
        n=10,
    ):
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
            bounds = (res.fs_v[max(idx - 1, 0)], res.fs_v[min(idx + 1, len(res) - 1)])
            step = bounds[1] - bounds[0]
        return res.assign(minVal=_res).iloc[idx]

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
