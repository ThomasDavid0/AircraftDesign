from logging import root
from typing import Callable
import numpy as np
import numpy.typing as npt
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import Literal
from acdesign.airfoils.airfoil import Airfoil


@dataclass
class ControlSurface:
    name: str
    root_prop: float
    tip_prop: float
    y_root: float = 0
    y_tip: float = 1
    sdup: float = 1.0

@dataclass
class WingPanel:
    b: float  # wingspan
    S: float  # wing area
    C: Callable[[npt.ArrayLike], npt.ArrayLike]
    le: Callable[[npt.ArrayLike], npt.ArrayLike]
    controls: list[ControlSurface] = None

    def add_control(self, control: ControlSurface):
        return WingPanel(
            self.b,
            self.S,
            self.C,
            self.le,
            controls=[*self.controls, control] if self.controls else [control],
        )

    @property
    def AR(self):
        return self.b**2 / self.S

    @property
    def root_chord(self) -> float:
        return self.C(0)

    @property
    def tip_chord(self) -> float:
        return self.C(1)

    @property
    def smc(self) -> float:
        return self.S / self.b

    @staticmethod
    def trapezoidal(b: float, S: float, TR: float, zerosweep: float = 0.25):
        Cr = 2 * S / (b * (1 + TR))
        Ct = TR * Cr

        def C(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr - (Cr - Ct) * y

        def le(y) -> npt.ArrayLike:
            return y * (Cr - Ct) * zerosweep

        return WingPanel(b, S, C, le)

    @staticmethod
    def trapz_crct(b: float, Cr: float, Ct: float, zerosweep: float = 0.25):
        S = b * (Cr + Ct) / 2
        return WingPanel.trapezoidal(b, S, Ct / Cr, zerosweep)

    @staticmethod
    def elliptical(b: float, S: float, tiploc: float = 0.25):
        Cr = 4 * S / (np.pi * b)

        def C(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr * np.sqrt(1 - y**2)

        def le(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr * tiploc * (1 - np.sqrt(1 - y**2))

        return WingPanel(b, S, C, le)
    

    @staticmethod
    def elliptical_cr(b: float, cr: float, tiploc: float = 0.25):
        S = np.pi * b * cr / 4
        return WingPanel.elliptical(b, S, tiploc)

    def plot(self, npoints=20):
        fig = go.Figure()
        y = np.linspace(0, 1, npoints)
        fig.add_trace(
            go.Scatter(
                x=y * self.b / 2, y=self.le(y), mode="lines", name="Leading Edge"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=y * self.b / 2,
                y=self.le(y) + self.C(y),
                mode="lines",
                name="Trailing Edge",
            )
        )
        return fig.update_layout(yaxis=dict(scaleanchor="x"))
