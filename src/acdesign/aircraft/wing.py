from dataclasses import dataclass
from typing import Literal
import numpy as np
import numpy.typing as npt
import pandas as pd
import plotly.graph_objects as go
from acdesign.airfoils.airfoil import Airfoil
from acdesign.airfoils.polar import UIUCPolar
from acdesign.avl.keywords import kwdict
from .wing_panel import WingPanel
from pathlib import Path
import shutil
from acdesign.avl.avl_runner import run_avl
from itertools import chain
from acdesign.avl.parse_avl_output import parse_strip_forces, parse_total_forces
from acdesign.performance.aero import WingAero

@dataclass
class Wing:
    """Assumes panels are connected sequentially from root to tip"""

    panels: list[WingPanel]

    @property
    def b(self) -> float:
        return sum([p.b for p in self.panels])

    @property
    def S(self) -> float:
        return sum([p.S for p in self.panels])

    @property
    def AR(self) -> float:
        return self.b**2 / self.S

    @property
    def smc(self) -> float:
        return self.S / self.b

    @property
    def bs(self):
        return np.array([p.b for p in self.panels])

    @property
    def ys(self):
        return self.bs.cumsum() / self.b

    def __repr__(self) -> str:
        return f"Wing(b={self.b:.2f}, S={self.S:.2f}, AR={self.AR:.2f}, smc={self.smc:.2f}, TR={self.C(1)[0] / self.C(0)[0]:.2f})"

    def get_panel(self, y: npt.ArrayLike):
        y = np.atleast_1d(y)
        assert y.ndim == 1
        ys = self.ys
        panel_lens = self.bs / self.b
        panel_id = len(ys) - (np.outer(y, np.ones_like(ys)) <= ys).sum(axis=1)
        y0s = np.array([0, *ys])
        panel_y = (y - y0s[panel_id]) / panel_lens[panel_id]
        return panel_id, np.clip(panel_y, 0, 1)

    def C(self, y: npt.NDArray) -> npt.ArrayLike:
        """Get chord at spanwise location y

        Args:
            y (npt.ArrayLike): spanwise location from 0 to 1

        Returns:
            npt.ArrayLike: chord at location y
        """
        y = np.atleast_1d(y)
        assert y.ndim == 1
        panel_id, panel_y = self.get_panel(y)
        return np.array([self.panels[id].C(y) for id, y in zip(panel_id, panel_y)])

    def le(self, y: npt.ArrayLike) -> npt.NDArray:
        y = np.atleast_1d(y)
        assert y.ndim == 1
        panel_id, panel_y = self.get_panel(y)
        return np.array([self.panels[id].le(y) for id, y in zip(panel_id, panel_y)])

    def plot(self, npoints: int = 100):
        fig = go.Figure()
        y = np.linspace(0, 1, npoints)
        fig.add_trace(
            go.Scatter(
                x=y * self.b / 2, y=self.le(y), mode="lines", line=dict(color="black"), name="Leading Edge"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=y * self.b / 2,
                y=self.le(y) + self.C(y),
                mode="lines",
                line=dict(color="black"),
                name="Trailing Edge",
                showlegend=False
            )
        )
        return fig.update_layout(yaxis=dict(scaleanchor="x"))

    def avl_surface(
        self, ylocs: npt.ArrayLike, sections: list[Airfoil] | Literal["flat"] = "flat"
    ):
        ylocs = np.atleast_1d(ylocs)
        odata = kwdict["SURFACE"]("Wing", 12, 0.0, 50, 0.0)

        le = self.le(ylocs)
        C = self.C(ylocs)
        y = ylocs * self.b / 2

        for i in range(len(ylocs)):
            odata += kwdict["SECTION"](le[i], y[i], 0, C[i], 0)
            Airfoil.parse_selig(
                "src/data/uiuc/" + sections[i].name + ".dat"
            ).dump_selig(f"avl/{sections[i].name}.dat")

            if sections != "flat":
                odata += kwdict["AFILE"](None, None, sections[i].name + ".dat")
        return odata

    def avl_header(self):
        return kwdict["HEADER"](
            "MACE 1", 0, 1, 0, 0, self.S, self.smc, self.b, -self.smc / 4, 0, 0
        )[1:]

    def dump_avl(
        self,
        file: Path,
        ylocs: npt.ArrayLike,
        sections: list[Airfoil] | Literal["flat"] = "flat",
    ):
        avldata = self.avl_surface(ylocs, sections)
        shutil.rmtree(file, ignore_errors=True)
        file.write_text("\n".join(self.avl_header() + avldata))

    def run_avl(
        self,
        cls: npt.ArrayLike,
        ylocs: npt.ArrayLike,
        sections: list[Airfoil] | Literal["flat"] = "flat",
    ):
        self.dump_avl(Path("avl/geom.avl"), ylocs, sections)
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
            parse_strip_forces(Path(f"avl/strip_forces_{i}.out"), self.b)
            for i in range(len(cls))
        ]

        loads = pd.concat(
            [
                pd.Series(parse_total_forces(Path(f"avl/total_forces_{i}.out")))
                for i in range(len(cls))
            ], keys=cls, axis=1
        ).T.reset_index().rename(columns=dict(index="Cl"))


        return loads, sloads

    def performance_wing(self, ylocs: list[float], polars: list[UIUCPolar]):
        return WingAero(
            self.b, self.S, polars, ylocs, self.C
        )
    
