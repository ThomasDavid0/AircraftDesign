from collections import namedtuple
import urllib.request
from importlib.resources import files
from io import TextIOWrapper
from typing import Literal
from urllib.error import HTTPError
from itertools import chain
from makefun import partial
import numpy as np
import xarray as xr
import pandas as pd
import numpy.typing as npt
from bs4 import BeautifulSoup
from .airfoil import Airfoil
from pathlib import Path

all_resources = files("data")


def getresource(name: str):
    return all_resources / name


class LFTDRGParser:
    def __init__(self, f: TextIOWrapper):
        self.f = f

    def read_all(self) -> pd.DataFrame:
        res = []
        while True:
            re = self.read_next_re_table()
            if re is None:
                break
            else:
                res.append(re)
        return pd.concat(res)

    def read_next_re_table(self) -> pd.DataFrame:
        for line in self.f:
            if "Average Reynolds #:" in line:
                re = float(self.f.readline().strip())
                break
        else:
            return None

        assert "Number of angles of attack:" in self.f.readline()
        n = int(self.f.readline().strip())

        headings = [h.strip() for h in self.f.readline().strip().split("/")]

        rows = [self.f.readline().strip().split() for _ in range(n)]

        if ">>>" in headings[-1]:
            headings = headings[:-1] + [f"scd{i}" for i in range(len(rows[0]) - 3)]

        df = pd.DataFrame(rows, columns=headings).astype("float").assign(re=re)

        cl_direction = np.sign(np.gradient(df.Cl)) if len(df) > 1 else np.ones(1)

        pre_stall = np.where(
            np.arange(len(df)) <= (cl_direction < 0).argmax(), True, False
        )

        return df.assign(pre_stall=pre_stall.astype(bool))


class UIUCPolar:
    def __init__(self, name: str, lift: pd.DataFrame, drag: pd.DataFrame):
        self.name = name
        self.lift = lift.assign(re=(20000 * (lift.re / 20000).round())).reset_index(
            drop=True
        )
        self.drag = drag.assign(re=(20000 * (drag.re / 20000).round())).reset_index(
            drop=True
        )

        self.res = self.drag.re.unique()

        self.pslift = self.lift.loc[self.lift.pre_stall]

        self.cl_to_cd = UIUCPolar.create_mapping(self.drag, "Cl", "Cd", 4)
        self.alpha_to_cl = UIUCPolar.create_mapping(self.pslift, "alpha", "Cl", 4)
        self.cl_to_cm = UIUCPolar.create_mapping(self.pslift, "Cl", "Cm", 4)
        self.alpha_to_cm = UIUCPolar.create_mapping(self.pslift, "alpha", "Cm", 4)
        self.cl_to_alpha = UIUCPolar.create_mapping(self.pslift, "Cl", "alpha", 4)


    def airfoil(self):
        return Airfoil.download(self.name.lower())

    @staticmethod
    def create_mapping(df: pd.DataFrame, source_col: str, target_col: str, degree=4):
        gb = df.groupby("re")
        res = np.array(list(gb.groups.keys()))
        polys = {
            re: partial(
                np.polyval, np.polyfit(grp[source_col], grp[target_col], deg=degree)
            )
            for re, grp in gb
        }

        def grid_mapping(
            re, input, coords: dict[str, npt.ArrayLike] | None = None
        ) -> xr.DataArray:
            """
            This will create a grid, x re, y input, z output
            if re and input are 2d arrays, the first column is the re or input value,
            the subseqsequent columns are values to tag onto the output array"""

            coords = coords if coords else {source_col: input, "re": re}
            coords = {k: np.atleast_1d(v) for k, v in coords.items()}

            re = np.atleast_1d(re)
            _re = np.clip(re, res.min(), res.max())  # the res we want to get cd at
            parm = np.atleast_1d(input)

            outputs = np.array(
                [polys[rei](parm) for rei in res]
            )  # the cds for each available poly

            results = np.array(
                [np.interp(_re, res, _outputs) for _outputs in outputs.T]
            )  # interpolate between the polys
            return xr.DataArray(
                np.atleast_2d(results),
                dims=list(coords.keys()),
                coords=coords,
            ).T

        def one_to_one_mapping(re: npt.NDArray, input: npt.NDArray) -> npt.NDArray:
            re = np.atleast_1d(re)
            input = np.atleast_1d(input)
            assert np.ndim(re) == 1, "re must be 1d array or scalar"
            assert np.ndim(input) == 1, "input must be 1d array or scalar"
            assert len(re) == len(input), "re and input must be same length"

            _re = np.clip(re, res.min(), res.max())
            outputs = np.array(
                [polys[rei](input) for rei in res]
            )  # the outputs for each available poly
            results = np.array(
                [np.interp(rei, res, _outputs) for (rei, _outputs) in zip(_re, outputs.T)]
            )  # interpolate between the polys

            return results.reshape(re.shape)

        Mappings = namedtuple("Mappings", ["grid", "oto"])
        return Mappings(grid=grid_mapping, oto=one_to_one_mapping)

    @property
    def minre(self):
        return self.lift.re.min()

    @property
    def maxre(self):
        return self.lift.re.max()

    def apply(
        self,
        re: npt.NDArray,
        cl_or_alpha: npt.NDArray,
        mode: Literal["cl", "alpha"] = "cl",
        mapping: Literal["grid", "oto"] = "grid",
    ) -> xr.DataArray:
        
        alpha_or_cl = (
            getattr(self.cl_to_alpha, mapping)(re, cl_or_alpha)
            if mode == "cl"
            else self.alpha_to_cl(re, cl_or_alpha)
        ).to_numpy()

        cm = (
            getattr(self.cl_to_cm, mapping)(re, cl_or_alpha)
            if mode == "cl"
            else self.alpha_to_cm(re, cl_or_alpha)
        ).to_numpy()

        cd = getattr(self.cl_to_cd, mapping)(
            re, cl_or_alpha if mode == "cl" else alpha_or_cl
        ).to_numpy()

        return xr.DataArray(
            np.stack(
                [
                    alpha_or_cl,
                    cm,
                    cd,
                ]
            ),
            dims=["result", "re", "cl" if mode == "cl" else "alpha"],
            coords={
                "result": ["alpha" if mode == "cl" else "cl", "Cm", "Cd"],
                "re": re,
                "cl" if mode == "cl" else "alpha": cl_or_alpha,
            },
        )

    def lookup(
        self,
        re: npt.ArrayLike | Literal["sweep"],
        cl_or_alpha: npt.ArrayLike | str | Literal["sweep"],
        mode="cl",
        n_re=50,
        n_cl=50,
        clipre: bool = True,
    ) -> pd.DataFrame:
        if isinstance(re, str) and re == "sweep":
            re = np.linspace(self.pslift.re.min(), self.pslift.re.max(), n_re)

        if clipre:
            re = np.clip(re, self.minre, self.maxre)
        if isinstance(cl_or_alpha, str) and cl_or_alpha == "sweep":
            if mode == "cl":
                cl_or_alpha = np.linspace(
                    self.pslift.Cl.min(), self.pslift.Cl.max(), n_cl
                )
            else:
                cl_or_alpha = np.linspace(
                    self.pslift.alpha.min(), self.pslift.alpha.max(), n_cl
                )

        re = np.atleast_1d(np.array(re))
        cl_or_alpha = np.atleast_1d(np.array(cl_or_alpha))

        assert re.ndim == 1
        assert cl_or_alpha.ndim == 1

        result = self.apply(re, cl_or_alpha, mode)

        gb = (
            result.to_dataframe(name="value")
            .reset_index(level="result")
            .groupby("result")
        )
        return pd.concat({k: v.rename(k) for k, v in gb["value"]}, axis=1).reset_index()

    def stall(self, re: npt.ArrayLike, n_cl=50, clipre: bool = True) -> pd.Series:
        df = self.lookup(re, cl_or_alpha="sweep", n_cl=n_cl, clipre=clipre)
        df = df.loc[~df.lift_warning.astype(bool)]

        return df.groupby("re").apply(
            lambda x: x.loc[x.cl.idxmax()], include_groups=False
        )

    @staticmethod
    def from_files(name, lft, drg):
        with open(lft, "r") as f:
            lftp = LFTDRGParser(f)
            lft = lftp.read_all()
        with open(drg, "r") as f:
            lftp = LFTDRGParser(f)
            drg = lftp.read_all()
        return UIUCPolar(name, lft, drg)

    @staticmethod
    def download(airfoil_name: str):
        return UIUCPolar.from_files(airfoil_name, *UIUCPolar._get_uiuc_files(airfoil_name))

    @staticmethod
    def local(airfoil_name: str):
        return UIUCPolar(
            airfoil_name,
            LFTDRGParser(getresource(f"uiuc/{airfoil_name}.LFT").open()).read_all(),
            LFTDRGParser(getresource(f"uiuc/{airfoil_name}.DRG").open()).read_all(),
        )

    #        return UIUCPolars.from_files(*[f"acdesign/data/uiuc/{airfoil_name}.{ld}" for ld in ["LFT", "DRG"]])

    @staticmethod
    def _get_uiuc_files(airfoil_name):
        for vol in range(1, 5):
            uiucurl = (
                f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/{airfoil_name}"
            )
            try:
                return [
                    urllib.request.urlretrieve(f"{uiucurl}.{ld}")[0]
                    for ld in ["LFT", "DRG"]
                ]
            except HTTPError:
                pass
            #try:
            #    dat = urllib.request.urlretrieve(f"https://m-selig.ae.illinois.edu/ads/coord/{airfoil_name}.dat")[0]
            #except HTTPError:
            #    dat = None
            
        else:
            return None

    def plot_drag_polar(self):
        import plotly.graph_objects as go

        fig = go.Figure()

        for re, df in self.drag.groupby("re"):
            fig.add_trace(
                go.Scatter(x=df["Cl"], y=df["Cd"], mode="lines", name=f"Re={re:.2e}")
            )
        return fig


def list_url_files(url, extension):
    resp = urllib.request.urlopen(url)
    soup = BeautifulSoup(resp, features="html.parser")

    files = [node.get("href") for node in soup.find_all("a")]
    return [f[:-4] for f in files if f.endswith(f".{extension}")]


def _list_uiucurl(vol):
    return list_url_files(f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/", "DRG")

def _list_dat_files():
    return list_url_files("https://m-selig.ae.illinois.edu/ads/coord_seligFmt/", ".dat")


def uiuc_airfoils():
    return list(chain(*[_list_uiucurl(i + 1) for i in range(4)]))

def local_uiuc_airfoils():
    return [f.stem for f in Path("src/data/uiuc").glob("*.LFT")]

def local_dat_airfoils():
    return [f.stem for f in Path("src/data/uiuc").glob("*.dat")]


def available_sections():
    uiuc = local_uiuc_airfoils()
    dat = local_dat_airfoils()
    
    return set(uiuc).intersection(set(dat))

def download_dat_files():
    airfoils = uiuc_airfoils()
    for lftfile in Path("src/data/uiuc").glob("*.LFT"):
        Airfoil.download(lftfile.stem, Path("src/data/uiuc"))
    
