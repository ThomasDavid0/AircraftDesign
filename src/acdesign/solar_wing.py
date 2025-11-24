from dataclasses import dataclass, field
from turtle import st

from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import WingPanel
from acdesign.performance.aero import WingAero
from acdesign.atmosphere import Atmosphere
import numpy as np
import numpy.typing as npt
import pandas as pd
from acdesign.performance.propulsion import (
    PropulsionSystem,
    FactorMotor,
    ConstantPropeller,
)
import plotly.graph_objects as go

pw = 0.13
propulsion = PropulsionSystem(
    propeller=ConstantPropeller(0.5, 3000),
    motor=FactorMotor(0.65),
)
atm = Atmosphere.alt(0)


@dataclass
class SolarWing:
    wing: Wing
    aero: WingAero
    npanels: int
    propulsion: PropulsionSystem = field(default_factory=lambda: propulsion)
    cell_power = 3

    def data(self):
        return {
            "npanels": self.npanels,
            "b": self.wing.b,
            "S": self.wing.S,
            "SMC": self.wing.smc,
            "AR": self.wing.AR,
            "TR": self.wing.C(1)[0] / self.wing.C(0)[0],
        }

    @staticmethod
    def straight(nrows, ncols, section):
        
        b = nrows * pw + 0.1
        C = ncols * pw + 0.1
        wing = Wing([WingPanel.trapezoidal(b, b * C, 1)])
        return SolarWing(
            wing,
            WingAero(b, b * C, [section], [0, 1]),
            len(SolarWing.place_panels(wing)) * 2,
        )

    @staticmethod
    def double_taper(nrows1, nrows2, ncols, section):
        b1 = nrows1 * pw + 0.05
        b2 = nrows2 * pw + 0.05
        b = b1 + b2
        CR = ncols * pw + 0.03 if ncols > 1 else ncols * pw + 0.1
        CT = pw + 0.05

        S = b1 * CR + b2 * (CR + CT) / 2
        wing = Wing(
            [
                WingPanel.trapezoidal(b1, b1 * CR, 1),
                WingPanel.trapz_crct(b2, CR, CT, 0.25),
            ]
        )
        return SolarWing(
            wing,
            WingAero(b, S, [section], [0, 1], wing.C),
            len(SolarWing.place_panels(wing)) * 2,  # for now assume 1 row in tip section
        )

    @staticmethod
    def straight_to_elliptical(nrows1, nrows2, ncols, section):
        """
        a = b2/2
        b = C/2
        x = chordwise location (0 to c/2)
        y = spanwise location (0 to b2/2)

        To get spanwise locations where each row of panels needs to stop:
        x**2 / a**2 + y**2 / b**2 = 1   # equation of ellipse
        y = sqrt( b**2 * ( 1 - x**2 / a**2)) # rearrange to get y

        Want y where x = 0.5 * (n * pw + 0.03), for n = 1 to ncols-1:

        y = sqrt( C**2 / 4 * (1 - 4 * (n * pw + 0.03) / b2**2))

        bb = nrows2 * pw
        bc = pw + 0.05
        """

        C = ncols * pw + 0.03
        Cm = pw + 0.03  # min chord at end of panels
        Ym = 0.5 * nrows2 * pw  # end of panels

        b2 = np.sqrt(4 * Ym**2 / (1 - Cm**2 / (4 * C**2)))

        b1 = nrows1 * pw + 0.05
        b = b1 + b2
        S = b1 * C + C * b2 * np.pi / 4

        wing = Wing(
            [
                WingPanel.trapezoidal(b1, b1 * C, 1),
                WingPanel.elliptical_cr(b2, C, 0.25),
            ]
        )

        return SolarWing(
            wing,
            WingAero(b, S, [section], [0, 1], wing.C),
            len(SolarWing.place_panels(wing)) * 2,  # for now assume 1 row in tip section
        )
    @staticmethod
    def ncols(wing: Wing, y: float, gap=0.025):
        """y in meters"""
        return ((wing.C(y * 2 / wing.b) - gap) // pw).astype(int)
    
    @staticmethod
    def place_panels(wing: Wing):
        
        y0 = 0.02
        panels = []
        fus_joint_added = False
        while y0 + pw < wing.b/2 and SolarWing.ncols(wing, y0+pw)[0]:
            if y0 > 0.7 and not fus_joint_added:
                y0 += 0.03
                fus_joint_added = True
            for panel in range(SolarWing.ncols(wing, y0+pw)[0]):
                x0=wing.le((y0) * 2 / wing.b)[0] + 0.015 + panel * pw
                panels.append((x0, y0))
            y0 += pw

        return panels

    def plot(self, fig, row=None, col=None):
        fig = go.Figure() if fig is None else fig
        y = np.linspace(0, 1, 100)
        yb = y * self.wing.b / 2

        fig.add_trace(
            go.Scatter(
                x=yb,
                y=self.wing.le(y),
                mode="lines",
                name="LE",
                line=dict(color="black"),
            ), row=row, col=col,
        )
        fig.add_trace(
            go.Scatter(
                x=yb,
                y=self.wing.le(y) + self.wing.C(y),
                mode="lines",
                name="TE",
                line=dict(color="black"),
            ), row=row, col=col,
        )

        
        panels = SolarWing.place_panels(self.wing)
        for x0, y0 in panels:
            fig.add_shape(
                xref='x', yref='y',
                type="rect",
                y0=x0, 
                x0=y0, 
                y1=x0 + pw, 
                x1=y0 + pw,
                row=row, col=col,
            )
        panels = np.array(panels)
        fig.add_trace(go.Scatter(
            x=panels[:,1] + pw/2,
            y=panels[:,0] + pw/2,
            mode="text",
            text=np.arange(len(panels))+1,
            marker=dict(color="red", size=2),
            name="Solar Cells",
        ), row=row, col=col
        )

        fig = fig.update_layout(
            yaxis=dict(scaleanchor="x", scaleratio=1)            
        )
        return fig

    def drag(
        self, atm: Atmosphere, v: npt.ArrayLike, lift: npt.ArrayLike, n: float = 50
    ):
        cls = self.aero.get_cl(atm, v, lift)

        loads, sloads = self.wing.run_avl(
            cls, ylocs=np.linspace(0, 1, n), sections=[self.aero.polars[0]] * n
        )

        wing_results = self.aero(atm, v, lift, sloads[-1], n=50, mode="oto")

        Cd = loads.CDind + wing_results.Cd0
        return 0.5 * atm.rho * v**2 * self.wing.S * Cd

    @property
    def solar_power(self):
        return self.npanels * self.cell_power

    def run(self, mass: npt.ArrayLike, airspeed: npt.ArrayLike, atm: Atmosphere, n: int = 50):
        
        odf = pd.DataFrame(dict(mass=mass, airspeed=airspeed, lift=mass*9.81))

        odf = odf.assign(cl=self.aero.get_cl(atm, airspeed, odf.lift))

        loads, sloads = self.wing.run_avl(
            odf.cl, ylocs=np.linspace(0, 1, n), sections=[self.aero.polars[0]] * n
        )

        odf = pd.concat([odf, loads.loc[:, ["CDind", "CDff", "e"]]], axis=1)

        # TODO just taking the last sload here, wont work if cl is 0.
        aero = self.aero(atm, odf.airspeed, odf.lift, sloads[-1], n=50, mode="oto")

        odf = odf.merge(aero.loc[:,["wing_l", "fs_v", "Cd0"]], left_on=["lift", "airspeed"], right_on=["wing_l", "fs_v"])

        odf = odf.assign(Cd = odf.CDind + odf.Cd0)
        odf = odf.assign(
            drag = 0.5 * atm.rho * odf.airspeed**2 * self.wing.S * odf.Cd
        )

        odf = odf.assign(
            power = self.propulsion(atm, odf.airspeed, odf.drag),
            solar_power = self.solar_power
        )

        return odf

    def max_mass(
        self,
        airspeed: npt.ArrayLike,
        atm: Atmosphere,
        min_mass: float = 6,
        max_mass: float = 15,
    ):
        masses = np.linspace(min_mass, max_mass, 30)

        mass, u = np.meshgrid(masses, np.atleast_1d(airspeed), indexing="ij")
        mass, u = mass.flatten(), u.flatten()

        odf = self.run(mass, u, atm)

    
        surplus = odf.solar_power > odf.power

        return odf.loc[surplus].groupby("airspeed").max().mass
