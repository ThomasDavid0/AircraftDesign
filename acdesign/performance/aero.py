
import numpy as np
import pandas as pd
from .operating_point import OperatingPoint
from acdesign.airfoils.polar import UIUCPolars
from typing import Dict, List
from scipy.optimize import minimize, Bounds
from collections import namedtuple
from acdesign.aircraft import Wing
from acdesign.base import Modifiable
from dataclasses import dataclass


@dataclass
class FuseAero(Modifiable):
    length: float
    diameter: float

    def __call__(self, op: OperatingPoint, cl:float=0.0):
        re = op.atm.rho * op.V * self.length / op.atm.mu
        return dict(
            S=self.length * np.pi * self.diameter, 
            c=self.length,
            Cl=0,
            Cd0=0.455/(np.log10(re)**2.58),
            Cd=0.455/(np.log10(re)**2.58),
            Cm=0,
            re=re
        )


@dataclass
class WingAero(Modifiable):
    b: float
    S: float
    polars: List[UIUCPolars]
    rib_locs: List[float]

    @property
    def smc(self):
        return self.S / self.b
    
    @property
    def AR(self):
        return self.b / self.smc

    def __call__(
        self, 
        op: OperatingPoint, 
        cl:float, 
        spanload=lambda yb: np.sqrt(1-yb**2),
        n=50,
        invert=False
    ):
        """Calculate the wing drag and moment Coefficients given the wing Cl.
        Assumes rectangular wing (span load distribution = span Cl distribution)

        Args:
            op (OperatingPoint): _description_
            cl (float): total lift coefficient
            spanload (_type_, optional): function to calculate the spanload distribution
                Defaults to lambdayb:np.sqrt(1-yb**2).
            n (int, optional): number of points to integrate over. Defaults to 100.

        Returns:
            dict: containing the wing S, c, Cl, Cd, re and Cm
        """
        fac = -1 if invert else 1
        
        re = op.atm.rho * op.V * self.smc / op.atm.mu
        
        sload = spanload(np.linspace(0,1,n))
        sload = sload / np.mean(sload) 
        
        polars = [p.lookup(np.full(len(sload), re), fac * cl * sload) for p in self.polars]
        
        sst = [(int(n*s0), int(n*s1)) for s0, s1 in zip(self.rib_locs[:-1], self.rib_locs[1:])]
        
        res = pd.concat([
            p.iloc[s[0]:s[1]] for s, p in zip(sst, polars)
        ]).mean(skipna=False)
#        eh = e_howe(op.V / 330, 0.65, np.radians(5), 1, 0.18, self.AR)
        k=1/(np.pi*self.AR)

        return dict(
            S=self.S, 
            c=self.smc,
            AR=self.AR,
            Cl=res.Cl*fac,
            Cd0=res.Cd,
            k=k,
            Cd=res.Cd + k * res.Cl**2,#0.02 + k * res.Cl**2,
            stall=np.any(res.stall),
            Cm=res.Cm*fac,
            re=re
        )
    

    @staticmethod
    def e_howe(M, lam, sw, Ne, toc, A):
        """calculation of oswald efficiency factor according to Howe 2000,
        ref https://www.fzt.haw-hamburg.de/pers/Scholz/HOOU/AircraftDesign_13_Drag.pdf
        M = flight mach number
        A = effective aspect ratio
        toc = thickness to chord ratio
        sw = sweep of 25% chord line
        Ne = number of engines on the wing
        lam = taper ratio
        """

        def f(lam):
            return 0.005 * (1 + 1.5 * (lam-0.6)**2)
        _a = 1 + 0.12*M**6
        _b = (0.142 + f(lam) * A * (10 * toc)*0.33) / np.cos(sw)*2
        _c = 0.1 * (3 * Ne + 1) / (4+A)**0.8
        return 1 / (_a * (1 + _b + _c))



@dataclass
class AircraftAero(Modifiable):
    wing: WingAero
    tail: WingAero
    fin: WingAero
    fus: FuseAero
    pw:float
    pt:float
    cd0_offset:float=0

    def get_moment(self, op: OperatingPoint, mass: float, tail_cl: float):
        #tail force +ve up
        tail = self.tail(op, tail_cl, invert=True)
        
        tail_force = op.Q * tail["S"] * tail_cl
        tail_moment = op.Q * tail["S"] * tail["Cm"] * tail["c"]

        wing_cl = (mass * 9.81 - tail_force) / (op.Q * self.wing.S) 
        wing_coeffs = self.wing(op, wing_cl)       
        wing_moment = op.Q * self.wing.S * self.wing.smc * wing_coeffs["Cm"]
        return wing_moment + tail_moment - \
            op.Q * self.wing.S * wing_cl * self.pw - tail_force * self.pt


    def quick_trim(self, op: OperatingPoint, mass: float):
        # this is not proper trimming but a guess that should be quicker than trim
        mom = self.get_moment(op, mass, 0.0)
        tfreq= mom / self.pt
        tclreq = tfreq / (op.Q * self.tail.S)
        wingcl = (mass * 9.81 + tfreq) / (op.Q * self.wing.S)
        
        df = pd.DataFrame(
            dict(
                wing=self.wing(op, wingcl),
                tail=self.tail(op, tclreq, invert=True),
                fin=self.fin(op, 0),
                fuse=self.fus(op),
            )
        ).T.assign(p=[self.pw, self.pt, 0, 0])
        
        return df.assign(
            gCl = df.Cl * df.S / self.wing.S, 
            gCd = df.Cd * df.S / self.wing.S,
            gCd0 = df.Cd0 * df.S / self.wing.S,
        )
        
    def trim(self, op: OperatingPoint, mass: float):
        # TODO this makes it too slow for geometry optimization
        tailcl = minimize(lambda tf: abs(self.get_moment(op, mass, tf)), 0.0, bounds=Bounds(-2, 2), method='Nelder-Mead').x
        tail_force = op.Q * self.tail.S * tailcl
        wingcl = (mass * 9.81 + tail_force) / (op.Q * self.wing.S)
        
        df = pd.DataFrame(
            dict(
                wing=self.wing(op, wingcl),
                tail=self.tail(op, tailcl, invert=True),
                fin=self.fin(op, 0),
                fuse=self.fus(op),
            )
        ).T.assign(p=[self.pw, self.pt, 0, 0])
        
        return df.assign(
            gCl = df.Cl * df.S / self.wing.S, 
            gCd = df.Cd * df.S / self.wing.S,
            gCd0 = df.Cd0 * df.S / self.wing.S,
        )

    @property
    def CLmax(self):
        return 1.1

    @property
    def S(self):
        return self.wing.S



