from json import dumps

from acdesign import AVL_WORKSPACE
from importlib.metadata import files
from pathlib import Path
from typing import Callable, Literal, overload
import numpy as np
import numpy.typing as npt
import plotly.graph_objects as go
from dataclasses import dataclass, field
from acdesign.airfoils.airfoil import Airfoil, InterpolatedAirfoil
from acdesign.types import FloatArrayT
import geometry as g
from acdesign.avl.keywords import kwdict


@dataclass
class ControlSurface:
    name: str
    root_prop: float
    tip_prop: float
    sdup: float = 1.0


@dataclass
class WingPanel:
    """Represents a single straight taper or elliptical section of a wing, with one full span control surface.
    wing defined from root to tip, or left to right if sym==False.

    Attributes:
        b: Wingspan along the panel (not necessarily horizontal).
        s: Wing area.
        _C: Function taking y (0 to 1) and returning chord length.
        _le: Function taking y (0 to 1) and returning leading edge x location.
        dihedral: Dihedral in radians; positive moves the tip up (negative body x rotation).
        sym: Whether the panel is symmetric about the centerline; if true ydupl will be set in AVL.
        airfoils: Airfoil mapping keyed by spanwise location between 0 and 1, or a single airfoil/"flat".
        ribs: Spanwise locations between 0 and 1 where ribs should be placed to describe the planform.
        control: Control surface, always full span of this panel.
    """

    b: float
    s: float
    _C: Callable[[FloatArrayT], FloatArrayT]
    _le: Callable[[FloatArrayT], FloatArrayT]
    dihedral: float = 0.0
    sym: bool = True
    airfoils: dict[float, Airfoil] = field(default_factory=lambda: {0: Airfoil.flat()})
    ribs: list[float] = field(default_factory=lambda: [0, 1])
    control: ControlSurface = None

    def __post_init__(self):
        self.S = self.s * np.cos(self.dihedral)
        self.AR = self.b**2 / self.s
        self.root_chord = self.C(0)
        self.tip_chord = self.C(1)
        self.smc = self.s / self.b

        self.all_ribs = np.array(sorted(
            list(set(self.ribs + list(self.airfoils.keys()) + [0.0, 1.0]))
        ))

        if self.control is not None and self.tip_chord == 0:
            raise ValueError(
                "Control surface cannot be placed on panel with zero tip chord"
            )

    def __repr__(self):
        return dumps(self.__dict__, indent=2, default=str)

    @overload
    def get_y(self, y: float, value: bool = False) -> float: ...
    @overload
    def get_y(self, y: FloatArrayT, value: bool = False) -> FloatArrayT: ...
    def get_y(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """Convert spanwise location or distance along panel to spanwise location"""
        if value:
            if self.sym:
                _y = y * 2 / self.b
            else:
                _y = y / self.b
        else:
            _y = y
        if np.any(_y > 1) or np.any(_y < 0):
            raise ValueError(
                "Attempt to get chord at spanwise location outside of panel"
            )
        return _y

    def y(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """get panel local y location at spanwise location or distance along panel"""
        y = self.get_y(y, value)
        return y * self.b

    def dihedral_rotation(self) -> g.Quaternion:
        return g.Quaternion.from_euler(g.PX(self.dihedral))

    def Y(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """get local y location at spanwise location or distance along panel"""
        return self.y(y, value) * np.cos(self.dihedral)

    def Z(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """Get Z location at spanwise location or distance along panel"""
        return self.y(y, value) * np.sin(self.dihedral)

    @overload
    def C(self, y: float, value: bool = False) -> float: ...
    @overload
    def C(self, y: FloatArrayT, value: bool = False) -> FloatArrayT: ...
    def C(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """Get chord length at spanwise location or distance along panel (if value is True)"""
        return self._C(self.get_y(y, value))

    @overload
    def le(self, y: float, value: bool = False) -> float: ...
    @overload
    def le(self, y: FloatArrayT, value: bool = False) -> FloatArrayT: ...
    def le(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        return self._le(self.get_y(y, value))

    def le_point(self, y: float | FloatArrayT) -> g.Point:
        return g.Point(-self.le(y), self.Y(y), self.Z(y))

    def te_point(self, y: float | FloatArrayT) -> g.Point:
        return g.Point(-self.le(y) - self.C(y), self.Y(y), self.Z(y))

    @staticmethod
    def trapezoidal(b: float, S: float, TR: float, zerosweep: float = 0.25, **kwargs):
        Cr = 2 * S / (b * (1 + TR))
        Ct = TR * Cr

        def C(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr - (Cr - Ct) * y

        def le(y: npt.ArrayLike) -> npt.ArrayLike:
            return y * (Cr - Ct) * zerosweep

        return WingPanel(b, S, C, le, **kwargs)

    @staticmethod
    def trapz_crct(b: float, Cr: float, Ct: float, *args, **kwargs):
        S = b * (Cr + Ct) / 2
        return WingPanel.trapezoidal(b, S, Ct / Cr, *args, **kwargs)

    @staticmethod
    def elliptical(
        b: float,
        S: float,
        ct: float = 0.0,
        tiploc: float = 0.25,
        **kwargs,
    ):
        # TODO handle non zero ct
        Cr = 4 * S / (np.pi * b)

        def C(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr * np.sqrt(1 - y**2)

        def le(y: npt.ArrayLike) -> npt.ArrayLike:
            return Cr * tiploc * (1 - np.sqrt(1 - y**2))

        if "ribs" not in kwargs:
            kwargs["ribs"] = (1 - np.logspace(0, -1, 10)) * 1 / 0.9

        return WingPanel(b, S, C, le, **kwargs)

    @staticmethod
    def elliptical_cr(b: float, cr: float, ct: float = 0.0, *args, **kwargs):
        # TODO handle non zero ct
        S = np.pi * b * cr / 4
        return WingPanel.elliptical(b, S, *args, **kwargs)

    def get_airfoil(self, y: float) -> Airfoil | InterpolatedAirfoil:
        for i, y1 in enumerate(self.airfoils.keys()):
            if y1 >= y:
                if y == y1:
                    return self.airfoils[y1]
                else:
                    y0 = list(self.airfoils.keys())[i - 1]
                    af0 = self.airfoils[y0]
                    af1 = self.airfoils[y1]
                    if af0.name == "flat" and af1.name == "flat":
                        return af0
                    return InterpolatedAirfoil.build(
                        af0,
                        af1,
                        (y - y0) / (y1 - y0),
                    )
        else:
            return self.airfoils[y1]

    def get_xhinge(self, y: float) -> float:
        """get the x/c location of the hinge at spanwise location y"""
        # st stands for equivalent straight taper
        st_y_prop = self.control.root_prop * (1 - y) + self.control.tip_prop * y
        st_le = self.le(0) * (1 - y) + self.le(1) * y
        st_c_y = self.C(0) * (1 - y) + self.C(1) * y

        wx_hinge_y = st_le + (1 - st_y_prop) * st_c_y

        return (wx_hinge_y - self.le(y)) / self.C(y)

    def create_avl_ribs(self, shift: g.Point = None):
        shift = shift or g.P0()
        odata = []

        le = (
            g.Point(
                self.le(self.all_ribs), self.Y(self.all_ribs), self.Z(self.all_ribs)
            )
            + shift
        )
        C = self.C(self.all_ribs)

        for i, y in enumerate(self.all_ribs):
            odata += kwdict["SECTION"](le.x[i], le.y[i], le.z[i], C[i], 0)

            airfoil = self.get_airfoil(y)
            if isinstance(airfoil, Airfoil) and airfoil.name == "flat":
                continue
            airfoil.dump_selig(Path(AVL_WORKSPACE) /  f"{airfoil.name}.dat")

            odata += kwdict["AFILE"](None, None, f"{airfoil.name}.dat")

            if self.control is not None:
                odata += kwdict["CONTROL"](
                    self.control.name,
                    1.0,
                    self.get_xhinge(y),
                    0.0,
                    0.0,
                    0.0,
                    self.control.sdup,
                )

        return odata

    def plot_planform(self, npoints: int = 100, fig=None):
        fig = go.Figure() if fig is None else fig
        y = np.linspace(0, 1, npoints)
        fig.add_trace(
            go.Scatter(
                x=self.y(y),
                y=self.le(y),
                mode="lines",
                name="Leading Edge",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self.y(y),
                y=self.le(y) + self.C(y),
                mode="lines",
                name="Trailing Edge",
                showlegend=False,
            )
        )
        for i, _y in enumerate(self.ribs):
            fig.add_trace(
                go.Scatter(
                    x=[self.y(_y), self.y(_y)],
                    y=[self.le(_y), self.le(_y) + self.C(_y)],
                    mode="lines",
                    name=f"Rib{i}",
                    showlegend=False,
                    line=dict(color="black", dash="dash"),
                )
            )

        for i, (_y, af) in enumerate(self.airfoils.items()):
            if af == "flat":
                continue
            fig.add_trace(
                go.Scatter(
                    x=[self.y(_y), self.y(_y)],
                    y=[self.le(_y), self.le(_y) + self.C(_y)],
                    mode="lines",
                    name=str(af),
                    showlegend=False,
                    line=dict(color="green", dash="solid"),
                )
            )

        if self.control is not None:
            fig.add_trace(
                go.Scatter(
                    x=[self.y(0), self.y(1)],
                    y=[
                        self.le(0) + self.get_xhinge(0) * self.C(0),
                        self.le(1) + self.get_xhinge(1) * self.C(1),
                    ],
                    mode="lines",
                    name=f"{self.control.name} hinge",
                    showlegend=False,
                    line=dict(color="red", dash="dot"),
                )
            )
        return fig.update_layout(yaxis=dict(scaleanchor="x"))

    def plot_3d(self, npoints: int = 100, shift: g.Point = None, fig=None):
        fig = go.Figure() if fig is None else fig
        y = np.linspace(0, 1, npoints)
        shift = shift or g.P0()
        fig.add_trace(
            go.Scatter3d(
                x=self.le(y) + shift.x,
                y=self.Y(y) + shift.y,
                z=self.Z(y) + shift.z,
                mode="lines",
                name="Leading Edge",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=self.le(y) + self.C(y) + shift.x,
                y=self.Y(y) + shift.y,
                z=self.Z(y) + shift.z,
                mode="lines",
                name="Trailing Edge",
                showlegend=False,
            )
        )

        if self.control is not None:
            fig.add_trace(
                go.Scatter3d(
                    x=self.le(y) + self.get_xhinge(y) * self.C(y) + shift.x,
                    y=self.Y(y) + shift.y,
                    z=self.Z(y) + shift.z,
                    mode="lines",
                    name=f"{self.control.name} hinge",
                    showlegend=False,
                    line=dict(color="red", dash="dot"),
                )
            )

        drot = self.dihedral_rotation()

        for i, _y in enumerate(self.ribs):
            _le = self.le_point(_y) + shift
            afoil = self.get_airfoil(_y)
            afpoints = (
                drot.transform_point(afoil.body_points() * self.C(_y)) + _le
            )

            fig.add_trace(
                go.Scatter3d(
                    x=afpoints.x,
                    y=afpoints.y,
                    z=afpoints.z,
                    mode="lines",
                    name=f"Airfoil{_y}",
                    showlegend=False,
                    line=dict(color="green", dash="solid"),
                )
            )
            afmcpoints = (
                drot.transform_point(afoil.body_points("mean_camber") * self.C(_y))
                + _le
            )
            fig.add_trace(
                go.Scatter3d(
                    x=afmcpoints.x,
                    y=afmcpoints.y,
                    z=afmcpoints.z,
                    mode="lines",
                    name=f"Mean Camber{_y}",
                    showlegend=False,
                    line=dict(color="blue", dash="dash"),
                )
            )

        for i, (_y, af) in enumerate(self.airfoils.items()):
            _le = self.le_point(_y) + shift
            afoil = drot.transform_point(af.body_points() * self.C(_y)) + _le

            fig.add_trace(
                go.Scatter3d(
                    x=afoil.x,
                    y=afoil.y,
                    z=afoil.z,
                    mode="lines",
                    name=f"Airfoil{_y}",
                    showlegend=False,
                    line=dict(color="blue", dash="solid", width=4),
                )
            )

            af_mc = (
                drot.transform_point(af.body_points("mean_camber") * self.C(_y))
                + _le
            )
            fig.add_trace(
                go.Scatter3d(
                    x=af_mc.x,
                    y=af_mc.y,
                    z=af_mc.z,
                    mode="lines",
                    name=f"Mean Camber{_y}",
                    showlegend=False,
                    line=dict(color="blue", dash="dash"),
                )
            )
        return fig.update_layout(scene=dict(aspectmode="data"))
