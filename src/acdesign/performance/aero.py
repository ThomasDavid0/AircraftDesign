
import numpy as np
import numpy.typing as npt
import pandas as pd

from acdesign.atmosphere import Atmosphere
from .operating_point import OperatingPoint
from acdesign.airfoils.polar import UIUCPolars
from typing import Dict, List
from scipy.optimize import minimize, Bounds
from acdesign.aircraft import Wing
from dataclasses import dataclass


@dataclass
class FuseAero:
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
class WingIncrement:
    C: float # chord
    b: float # span
    x: float # x location
    y: float # spanwise location
    polar: UIUCPolars

    @property
    def S(self):
        return self.b * self.C

    def __call__(self, atm: Atmosphere, v: npt.ArrayLike, lift: float):
        q = 0.5 * atm.rho * v**2
        re = atm.rho * v * self.C / atm.mu
        cl = lift / (q * self.S )
        polars = self.polar.lookup(re, cl, "cl")
        return polars.assign(
            re = re,
            drag = q * self.S  * polars.Cd,
            moment = lift * self.x + q * self.S * self.C * polars.Cm,
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
    polars: List[UIUCPolars]
    rib_locs: List[float]

    @property
    def smc(self):
        return self.S / self.b
    
    @property
    def AR(self):
        return self.b / self.smc
    
    def stall(self, op: OperatingPoint, spanload=lambda yb: np.sqrt(1-yb**2)):
        """get the minimum Cl at which any section stalls"""
        re = op.atm.rho * op.V * self.smc / op.atm.mu

        loads = spanload(np.array(self.rib_locs[:-1]))
        clmax = pd.DataFrame([polar.stall(re).iloc[0] for polar in self.polars])
        
        rib_stall_ratio = clmax.cl / loads
        critical_rib = rib_stall_ratio.to_numpy().argmin()

        local_stall = clmax.iloc[critical_rib]

        stall_cl = local_stall.cl / loads[critical_rib]

        return self(op, stall_cl, spanload)
        

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
            n (int, optional): number of points to integrate over. Defaults to 50.

        Returns:
            dict: containing the wing S, c, Cl, Cd, re and Cm
        """
        fac = -1 if invert else 1
        
        re = op.atm.rho * op.V * self.smc / op.atm.mu
        
        sload = spanload(np.linspace(0,1,n))
        sload = sload / np.mean(sload) 
        
        polars = [p.lookup(re, fac * cl * sload) for p in self.polars]
        
        sst = [(int(n*s0), int(n*s1)) for s0, s1 in zip(self.rib_locs[:-1], self.rib_locs[1:])]
        
        res = pd.concat([
            p.iloc[s[0]:s[1]] for s, p in zip(sst, polars)
        ]).mean(skipna=False)
#        eh = e_howe(op.V / 330, 0.65, np.radians(5), 1, 0.18, self.AR)
        k=1/(0.7*np.pi*self.AR)  # TODO assumed e of 0.7

        return dict(
            S=self.S, 
            c=self.smc,
            AR=self.AR,
            Cl=res.cl*fac,
            Cd0=res.Cd,
            k=k,
            Cd=res.Cd + k * res.cl**2,#0.02 + k * res.Cl**2,
            stall=np.any(res.lift_warning),
            Cm=res.Cm*fac,
            re=re
        )
    

    @staticmethod
    def e_howe(
        M , # mach number
        lam, # taper ratio
        sw, # 1/4 chord sweep, radians
        Ne, # number of engines on the wing
        toc, # thickness to chord ratio
        A # effective aspect ratio
    ):
        """calculation of oswald efficiency factor according to Howe 2000,
        ref https://www.fzt.haw-hamburg.de/pers/Scholz/HOOU/AircraftDesign_13_Drag.pdf
        """

        def f(lam):
            return 0.005 * (1 + 1.5 * (lam-0.6)**2)
        _a = 1 + 0.12*M**6
        _b = (0.142 + f(lam) * A * (10 * toc)*0.33) / np.cos(sw)*2
        _c = 0.1 * (3 * Ne + 1) / (4+A)**0.8
        return 1 / (_a * (1 + _b + _c))



@dataclass
class AircraftAero:
    wing: WingAero
    tail: WingAero
    fin: WingAero
    fus: FuseAero
    pw:float
    pt:float
    cd0_offset:float=0

    def get_moment(self, op: OperatingPoint, lift: float, tail_cl: float):
        #tail force +ve up
        tail = self.tail(op, tail_cl, invert=True)
        
        tail_force = op.Q * tail["S"] * tail_cl
        tail_moment = op.Q * tail["S"] * tail["Cm"] * tail["c"]

        wing_cl = (lift - tail_force) / (op.Q * self.wing.S) 
        wing_coeffs = self.wing(op, wing_cl)       
        wing_moment = op.Q * self.wing.S * self.wing.smc * wing_coeffs["Cm"]
        return wing_moment + tail_moment - \
            op.Q * self.wing.S * wing_cl * self.pw - tail_force * self.pt


    def quick_trim(self, op: OperatingPoint, lift: float):
        # this is not proper trimming but a guess that should be quicker than trim
        mom = self.get_moment(op, lift, 0.0)
        tfreq= mom / self.pt
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
            gCl = df.Cl * df.S / self.wing.S, 
            gCd = df.Cd * df.S / self.wing.S,
            gCd0 = df.Cd0 * df.S / self.wing.S,
        )
        
    def trim(self, op: OperatingPoint, lift: float):
        # TODO this makes it too slow for geometry optimization
        tailcl = minimize(lambda tf: abs(self.get_moment(op, lift, tf)), 0.0, bounds=Bounds(-2, 2), method='Nelder-Mead').x
        tail_force = op.Q * self.tail.S * tailcl
        wingcl = (lift * 9.81 + tail_force) / (op.Q * self.wing.S)
        
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

    def calculate_drag(self, op: OperatingPoint, lift: float):
        trim = self.trim(op, lift)
        stall = np.any(trim.stall)
        cd = 1 if stall else np.sum(trim.gCd)

        return op.Q * self.S * (cd + self.cd0_offset)

    
    def stall_lift(self, op: OperatingPoint):
        # get Cl at which the main wing stalls

        pass

    def stall_speed(self, atm: Atmosphere, lift: float, n=50):
        v = np.linspace(5, 20)
        res = np.array([self.trim(OperatingPoint(atm, v), lift).wing["stall"] for v in v])
        return v[np.argmin(res)]

    @property
    def CLmax(self):
        return 1.1

    @property
    def S(self):
        return self.wing.S



