
import numpy as np
import pandas as pd
from .operating_point import OperatingPoint
from acdesign.airfoils.polar import UIUCPolars
from typing import Dict, List
from scipy.optimize import minimize
from collections import namedtuple
from acdesign.aircraft import Wing



class FuseAero:
    def __init__(self, length, diameter):
        self.length = length
        self.diameter = diameter
        self.ld = length/diameter
        self.f = 1 + 2.2 / np.sqrt(self.ld) - 0.9 / (self.ld**3)
        self.swet = self.length * np.pi * self.diameter

    def __call__(self, op: OperatingPoint, cl:float=0.0):
        re = op.atm.rho * op.V * self.length / op.atm.mu
        return dict(
            S=self.swet, 
            c=self.length,
            Cl=0,
            Cd0=0.455/(np.log10(re)**2.58),
            Cd=0.455/(np.log10(re)**2.58),
            Cm=0,
            re=re
        )

class WingAero:
    def __init__(self, b, S, polars: List[UIUCPolars], rib_locs: List[float]):
        self.b = b
        self.S = S
        self.polars = polars
        self.rib_locs = rib_locs
        self.smc = self.S / self.b
        self.AR = self.b / self.smc

    def __call__(
        self, 
        op: OperatingPoint, 
        cl:float, 
        spanload=lambda yb: np.sqrt(1-yb**2),
        n=100
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
        re = op.atm.rho * op.V * self.smc / op.atm.mu
        
        sload = spanload(np.linspace(0,1,n))
        sload = sload / np.mean(sload) 
        
        polars = [p.lookup(re, cl * sload) for p in self.polars]
        
        sst = [(int(n*s0), int(n*s1)) for s0, s1 in zip(self.rib_locs[:-1], self.rib_locs[1:])]
        
        res = pd.concat([
            p.iloc[s[0]:s[1]] for s, p in zip(sst, polars)
        ]).mean()
        eh = e_howe(op.V / 330, 0.65, np.radians(5), 1, 0.18, self.AR)
        k=1/(eh*np.pi*self.AR)

        return dict(
            S=self.S, 
            c=self.smc,
            Cl=res.Cl,
            Cd0=res.Cd,
            k=k,
            Cd=res.Cd + k * res.Cl**2,
            Cm=res.Cm,
            re=re
        )
    


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




class AircraftAero:
    def __init__(self, wing: WingAero, tail: WingAero, fus: FuseAero, pw:float, pt:float):
        self.wing = wing
        self.tail = tail
        self.fus = fus
        self.pw = pw
        self.pt = pt


    def get_moment(self, op: OperatingPoint, mass: float, tail_cl: float):
        #tail force +ve up
        tail = self.tail(op, tail_cl)
        
        tail_force = op.Q * tail["S"] * tail_cl
        tail_moment = op.Q * tail["S"] * tail["Cm"] * tail["c"]

        wing_cl = (mass * 9.81 - tail_force) / op.Q * self.wing.S 
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
                tail=self.tail(op, tclreq),
                fuse=self.fus(op),
            )
        ).T.assign(p=[self.pw, self.pt, 0])
        
        return df.assign(
            gCl = df.Cl * df.S / self.wing.S, 
            gCd = df.Cd * df.S / self.wing.S,
            gCd0 = df.Cd0 * df.S / self.wing.S,
        )
        
    def trim(self, op: OperatingPoint, mass: float):
        # TODO this makes it too slow for geometry optimization
        tailcl = minimize(lambda tf: abs(self.get_moment(op, mass, tf)), -0.5).x
        tail_force = op.Q * self.tail.S * tailcl
        wingcl = (mass * 9.81 + tail_force) / (op.Q * self.wing.S)
        
        df = pd.DataFrame(
            dict(
                wing=self.wing(op, wingcl),
                tail=self.tail(op, tailcl),
                fuse=self.fus(op),
            )
        ).T.assign(p=[self.pw, self.pt, 0])
        
        return df.assign(
            gCl = df.Cl * df.S / self.wing.S, 
            gCd = df.Cd * df.S / self.wing.S,
            gCd0 = df.Cd0 * df.S / self.wing.S,
        )

    @property
    def CLmax(self):
        return 1.5

    @property
    def S(self):
        return self.wing.S



