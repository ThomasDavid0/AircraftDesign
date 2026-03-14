from pathlib import Path
from dataclasses import dataclass
from typing import Literal
import urllib.request
from geometry import Point, PY
import geometry as g
from httpx import get
import numpy as np
from scipy.interpolate import interp1d
import shutil


@dataclass
class Airfoil:
    name: str
    points: Point  # this is on the X Y plane, x is chordwise, y is thickness direction, z is zero

    def __post_init__(self):
        self.le_point = self.points[int(self.points.minloc().x)]
        self.te_point = 0.5 * (self.points[0] + self.points[-1])
        self.te_thickness = (self.points[0].y - self.points[-1].y)[0]
        self.chord = self.points.x[0]
        self.top_surface = self.points[: self.points.minloc().x[0] + 1]
        self.btm_surface = self.points[self.points.minloc().x[0] :]

        self.top_func = interp1d(
            self.top_surface.x, self.top_surface.y, "cubic", fill_value="extrapolate"
        )
        self.btm_func = interp1d(
            self.btm_surface.x, self.btm_surface.y, "cubic", fill_value="extrapolate"
        )

        self.thickness = max(self.points.y) - min(self.points.y)

        self.mean_camber = 0.5 * g.PY(
            self.top_func(self.top_surface.x) + self.btm_func(self.top_surface.x)
        ) + g.PX(self.top_surface.x)

    def __str__(self):
        return self.name

    def body_points(self, group: str = "points"):
        """The points of the airfoil in the avl body frame (x aft, y right, z up)"""
        points = getattr(self, group)
        return g.Point(points.x, np.zeros_like(points.x), points.y)

    def camber(self, x):
        return 0.5 * (self.top_func(x) + self.btm_func(x))

    def dump_selig(self, file: str | Path):
        with open(file, "w") as f:
            f.write(f"{self.name}\n")
            for p in self.points:
                f.write(f"{p.x[0]:.6f} {p.y[0]:.6f}\n")

    @staticmethod
    def flat(name: str = "flat"):

        return Airfoil(
            name,
            Point.concatenate(
                [g.PX() * np.linspace(1, 0, 10), g.PX() * np.linspace(0.1, 1, 9)]
            ),
        )

    @staticmethod
    def parse_selig(file: str | Path, name_override: str = None):

        with open(file) as f:
            lines = [l.strip() for l in f.readlines()]
        name = lines[0]
        lines = lines[1:]

        if name_override is not None:
            name = name_override

        if lines[1] == "":
            npoints = np.array([float(v) for v in lines[0].split()]).astype("int")

            lines = lines[2:]

            d1 = lines[: npoints[0]]
            d2 = lines[npoints[0] + 1 :]
            if d1[0] == d2[0]:
                d1 = d1[1:]
            lines = list(reversed(d1)) + d2

        data = np.array([l.split() for l in lines]).astype(float)

        return Airfoil(name, Point(np.append(data, np.zeros((len(data), 1)), axis=1)))

    @staticmethod
    def local(name: str):
        return Airfoil.parse_selig(Path(f"src/data/uiuc/{name}.dat"))

    @staticmethod
    def download(airfoilname: str, outfolder: Path = None):
        # https://m-selig.ae.illinois.edu/ads/coord_updates/la5055.dat
        name = airfoilname.lower()
        name = name[-3] if name.endswith("-il") else name
        #            _file = urllib.request.urlretrieve("http://airfoiltools.com/airfoil/seligdatfile?airfoil=" + airfoiltoolsname)
        try:
            _file = urllib.request.urlretrieve(
                f"https://m-selig.ae.illinois.edu/ads/coord_seligFmt/{name}.dat"
            )
        except Exception as e:
            print("cannot find airfoil ", airfoilname)
            return None

        if outfolder is not None:
            if (Path(outfolder) / f"{airfoilname}.dat").exists():
                print(f"cannot write {name} to {airfoilname}.dat, already exists")
            else:
                shutil.copy(_file[0], outfolder / f"{airfoilname}.dat")
        return Airfoil.parse_selig(_file[0], name)

    def set_te_thickness(self, thick: float):
        surfaces = -np.sign(np.gradient(self.points.x))

        xunit = self.points.x / self.chord

        te_diff = (
            PY(0.5 * (thick - self.te_thickness), len(self.points)) * xunit * surfaces
        )

        return Airfoil(self.name, self.points + te_diff)

    def set_chord(self, chord):
        return Airfoil(self.name, self.points * chord / self.chord)

    def plot(self, fig=None, row=None, col=None):
        import plotly.graph_objects as go

        fig = fig if fig else go.Figure()
        fig.add_trace(
            go.Scatter(
                x=self.points.x,
                y=self.points.y,
                mode="lines",
                name=self.name,
                line=dict(width=2, color="black"),
            ),
            row=row,
            col=col,
        )
        fig.update_layout(yaxis=dict(scaleanchor="x"))
        return fig


@dataclass
class InterpolatedAirfoil(Airfoil):
    inbd: Airfoil
    otbd: Airfoil
    prop: float

    @staticmethod
    def build(inbd: Airfoil, otbd: Airfoil, prop: float):

        def top_func(x):
            return (1 - prop) * inbd.top_func(x) + prop * otbd.top_func(x)

        def btm_func(x):
            return (1 - prop) * inbd.btm_func(x) + prop * otbd.btm_func(x)

        top_surface = g.PY(top_func(inbd.top_surface.x)) + g.PX(inbd.top_surface.x)
        btm_surface = g.PY(btm_func(inbd.btm_surface.x[1:])) + g.PX(
            inbd.btm_surface.x[1:]
        )

        points = g.Point.concatenate([top_surface, btm_surface])

        return InterpolatedAirfoil(
            f"{inbd.name}_{prop:.2f}_{otbd.name}",
            points,
            inbd,
            otbd,
            prop,
        )
