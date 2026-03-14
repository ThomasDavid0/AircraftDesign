from dataclasses import dataclass, replace
from typing import Iterable, overload
import numpy as np
import numpy.typing as npt
import pandas as pd
import plotly.graph_objects as go
from acdesign.airfoils.polar import UIUCPolar
from acdesign.avl.keywords import kwdict
from acdesign.environment import AVL_WORKSPACE
from .wing_panel import WingPanel, ControlSurface
from pathlib import Path
import shutil
from acdesign.avl.avl_runner import run_avl
from itertools import chain
from acdesign.avl.parse_avl_output import parse_strip_forces, parse_total_forces
from acdesign.performance.aero import WingAero
from acdesign.types import FloatArrayT
import geometry as g


@dataclass
class Wing:
    """
    Represents a single surface in AVL.
    Comprises a list of panels connected sequentially from root to tip.
    """
    name: str
    offset: g.Point
    panels: list[WingPanel]

    def __post_init__(self):
        self.bs = np.array([p.b for p in self.panels])
        self.b = sum(self.bs)
        self.ys = self.bs.cumsum() / self.b
        self.ybs = self.bs / self.b

        self.Ys = np.array([p.Y(1) for p in self.panels]).cumsum()
        self.Zs = np.array([p.Z(1) for p in self.panels]).cumsum()

        self.ss = np.array([p.s for p in self.panels])
        self.s = sum(self.ss)
        self.Ss = np.array([p.S for p in self.panels])
        self.S = sum(self.Ss)
        self.AR = self.b**2 / self.s
        self.smc = self.s / self.b

        if any(p.sym != self.panels[0].sym for p in self.panels):
            raise ValueError("Inconsistent panel symmetry definitions")
        self.sym = self.panels[0].sym

    @overload
    def get_y(self, y: float, value: bool = False) -> float: ...
    @overload
    def get_y(self, y: FloatArrayT, value: bool = False) -> FloatArrayT: ...
    def get_y(self, y: FloatArrayT | float, value: bool = False) -> FloatArrayT | float:
        """Convert spanwise location or distance along panel to spanwise location"""
        _y = y * 2 / self.b if value else y
        if np.any(_y > 1) or np.any(_y < 0):
            raise ValueError(
                "Attempt to get chord at spanwise location outside of panel"
            )
        return _y

    def __len__(self):
        return len(self.panels)

    def __repr__(self) -> str:
        return f"Wing(b={self.b:.2f}, S={self.S:.2f}, AR={self.AR:.2f}, smc={self.smc:.2f}, TR={self.C(1)[0] / self.C(0)[0]:.2f})"

    def set_control(self, control: ControlSurface):
        """Adds a control to each surface, corrects the C for each panel"""
        return replace(
            self,
            panels=[
                replace(
                    p,
                    control=ControlSurface(
                        control.name,
                        control.root_prop * p.C(0) / self.C(0),
                        control.tip_prop * p.C(1) / self.C(1),
                        control.sdup,
                    ),
                )
                for p in self.panels
                if p.C(1) > 0
            ],
        )

    @overload
    def get_panel(
        self, y: float, otbd: bool = False, value: bool = False
    ) -> tuple[int, float]: ...
    @overload
    def get_panel(
        self, y: Iterable[float], otbd: bool = False, value: bool = False
    ) -> Iterable[tuple[int, float]]: ...
    def get_panel(
        self, y: Iterable[float] | float, otbd: bool = False, value: bool = False
    ) -> Iterable[tuple[int, float]] | tuple[int, float]:
        """Get panel id and spanwise location within panel for given spanwise location on wing
        if the spanwise location is at a panel intersection the panel closer to the root is returned
            unless otbd is True.

        """
        if pd.api.types.is_list_like(y):
            return y.__class__(self.get_panel(yi, otbd, value) for yi in y)

        _y = self.get_y(y, value)

        yarr = np.full(len(self.panels), _y)
        panel_id = len(self) - ((yarr < self.ys) if otbd else (yarr <= self.ys)).sum()
        y0s = np.array([0, *self.ys])
        panel_y = (y - y0s[panel_id]) / self.ybs[panel_id]
        return panel_id, np.clip(panel_y, 0, 1)

    @overload
    def C(self, y: float, otbd: bool = False, value: bool = False) -> float: ...
    @overload
    def C(self, y: Iterable, otbd: bool = False, value: bool = False) -> Iterable: ...
    def C(
        self, y: Iterable | float, otbd: bool = False, value: bool = False
    ) -> Iterable | float:
        if pd.api.types.is_list_like(y):
            return y.__class__(self.C(yi, otbd, value) for yi in y)

        panel_id, panel_y = self.get_panel(y, otbd, value)

        return self.panels[panel_id].C(panel_y)

    @overload
    def le(self, y: float, otbd: bool = False, value: bool = False) -> float: ...
    @overload
    def le(self, y: Iterable, otbd: bool = False, value: bool = False) -> Iterable: ...
    def le(
        self, y: Iterable | float, otbd: bool = False, value: bool = False
    ) -> Iterable | float:
        if pd.api.types.is_list_like(y):
            return y.__class__(self.C(yi, otbd, value) for yi in y)
        panel_id, panel_y = self.get_panel(y, otbd, value)
        return self.panels[panel_id].le(panel_y)

    def y(
        self, y: Iterable | float, otbd: bool = False, value: bool = False
    ) -> Iterable | float:
        if pd.api.types.is_list_like(y):
            return y.__class__(self.C(yi, otbd, value) for yi in y)
        panel_id, panel_y = self.get_panel(y, otbd, value)
        return self.panels[panel_id].y(panel_y)

    def plot(
        self,
        npoints: int = 100,
        shift: g.Point = None,
        fig: go.Figure = None,
        mode="lines",
    ) -> go.Figure:
        fig = fig or go.Figure()
        
        origin = self.offset + (shift or g.P0())
        for panel in self.panels:
            panel.plot_3d(npoints, origin, fig)
            origin += panel.le_point(1.0)
        return fig

    def dump_avl(self, component: int = None, translate: g.Point = None):

        odata = [""]
        odata += kwdict["SURFACE"](self.name, 12, 1.0, 20, 1.0)

        if component is not None:
            odata += kwdict["COMPONENT"](component)

        if self.sym:
            odata += kwdict["YDUPLICATE"](0.0)

        translate = (translate or g.Point(0, 0, 0)) + self.offset
    
        odata += kwdict["TRANSLATE"](
            translate.x[0], translate.y[0], translate.z[0]
        )

        shift = g.P0()
        for i, p in enumerate(self.panels):
            odata += p.create_avl_ribs(shift)
            shift = shift + p.le_point(1.0)

        return odata

    def avl_file(self, file: Path):
        avldata = self.dump_avl()
        shutil.rmtree(file, ignore_errors=True)
        avl_header = kwdict["HEADER"](
            "ACDesWing", 0, 1, 0, 0, self.S, self.smc, self.b, self.smc / 4, 0, 0
        )[1:]
        file.write_text("\n".join(avl_header + avldata))

    def run_avl(
        self,
        cls: npt.ArrayLike,
    ):
        self.avl_file(Path(AVL_WORKSPACE) / "geom.avl")
        cls = np.atleast_1d(cls)
        assert cls.ndim == 1
        for i in range(len(cls)):
            Path(f"avl/strip_forces_{i}.out").unlink(missing_ok=True)
            Path(f"avl/total_forces_{i}.out").unlink(missing_ok=True)

        run_avl(
            [
                "load geom.avl",
                "OPER",
                *chain(
                    *[
                        [
                            f"a c {cl}",
                            "x",
                            f"ft total_forces_{i}.out",
                            f"fs strip_forces_{i}.out",
                        ]
                        for i, cl in enumerate(cls)
                    ]
                ),
                "",
                "QUIT",
            ]
        )

        sloads = [
            parse_strip_forces(Path(AVL_WORKSPACE) / f"strip_forces_{i}.out", self.b)
            for i in range(len(cls))
        ]

        loads = (
            pd.concat(
                [
                    pd.Series(parse_total_forces(Path(AVL_WORKSPACE) /  f"total_forces_{i}.out"))
                    for i in range(len(cls))
                ],
                keys=cls,
                axis=1,
            )
            .T.reset_index()
            .rename(columns=dict(index="Cl"))
        )

        return loads, sloads

    def performance_wing(self, ylocs: list[float], polars: list[UIUCPolar]):
        return WingAero(self.b, self.S, polars, ylocs, self.C)
