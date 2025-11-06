import urllib.request
from importlib.resources import files
from io import TextIOWrapper
from numbers import Number
from typing import Literal
from urllib.error import HTTPError

import numpy as np
import xarray as xr
import pandas as pd
import numpy.typing as npt
from bs4 import BeautifulSoup
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

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

        pre_stall = np.where(np.arange(len(df)) <=(cl_direction < 0).argmax(), True, False)

        return df.assign(pre_stall=pre_stall.astype(bool))


def linear_or_nearest(points, values):
    linear = LinearNDInterpolator(points, values)
    nearest = NearestNDInterpolator(points, values)

    def inner(x):
        lin = linear(x)
        near = nearest(x)
        warn = np.isnan(lin)
        lin[warn] = near[warn]
        return lin, warn

    return inner


class UIUCPolars:
    def __init__(self, lift: pd.DataFrame, drag: pd.DataFrame):
        self.lift = (
            lift.assign(re=(5000 * (lift.re / 5000).round()))
            .reset_index(drop=True)
        )
        self.drag = (
            drag.assign(re=(5000 * (drag.re / 5000).round()))
            .reset_index(drop=True)
        )

        self.pslift = self.lift.loc[self.lift.pre_stall]

        self.alpha_to_cl = linear_or_nearest(
            (self.pslift.re/100000, self.pslift.alpha), self.pslift.Cl
        )
        self.cl_to_alpha = linear_or_nearest(
            (self.pslift.re/100000, self.pslift.Cl), self.pslift.alpha
        )
        self.cl_to_cm = linear_or_nearest(
            (self.pslift.re/100000, self.pslift.Cl), self.pslift.Cm
        )

        self.cl_to_cd = linear_or_nearest((self.drag.re/100000, self.drag.Cl), self.drag.Cd)

    @property
    def minre(self):
        return self.lift.re.min()

    @property 
    def maxre(self):
        return self.lift.re.max()
    

    def apply(self, re: npt.NDArray, cl_or_alpha: npt.NDArray, mode: Literal["cl", "alpha"] = "cl") -> xr.DataArray:

        recl = np.stack([np.tile(re/100000, (len(cl_or_alpha), 1)), np.tile(cl_or_alpha, (len(re), 1)).T]).T

        alpha_or_cl, lift_warning = self.cl_to_alpha(recl) if mode == "cl" else self.alpha_to_cl(recl)

        cm, _ = self.cl_to_cm(recl)
        cd, drag_warning = self.cl_to_cd(recl)

        return xr.DataArray(
            np.stack(
                [
                    alpha_or_cl,
                    cm,
                    cd,
                    lift_warning,
                    drag_warning,
                ]
            ),
            dims=["result", "re", "cl" if mode=="cl" else "alpha"],
            coords={
                "result": ["alpha" if mode=="cl" else "cl", "Cm", "Cd", "lift_warning", "drag_warning"],
                "re": re,
                "cl" if mode=="cl" else "alpha": cl_or_alpha,
            },
        )


    def lookup(
        self,
        re: npt.ArrayLike | Literal["sweep"],
        cl_or_alpha: npt.ArrayLike | str | Literal["sweep"],
        mode="cl",
        n_re=50,
        n_cl=50,
        clipre:bool=True
    ) -> pd.DataFrame:
        if isinstance(re, str) and re == "sweep":
            re = np.linspace(self.pslift.re.min(), self.pslift.re.max(), n_re)

        if clipre:
            re = np.clip(re, self.minre, self.maxre)
        if isinstance(cl_or_alpha, str) and cl_or_alpha == "sweep":
            if mode == "cl":
                cl_or_alpha = np.linspace(self.pslift.Cl.min(), self.pslift.Cl.max(), n_cl)
            else:
                cl_or_alpha = np.linspace(self.pslift.alpha.min(), self.pslift.alpha.max(), n_cl)
            

        re = np.atleast_1d(np.array(re))
        cl_or_alpha = np.atleast_1d(np.array(cl_or_alpha))

        assert re.ndim == 1
        assert cl_or_alpha.ndim == 1

        result = self.apply(re, cl_or_alpha, mode)

        gb = result.to_dataframe(name="value").reset_index(level="result").groupby("result")
        return pd.concat({k: v.rename(k) for k,v in gb['value']}, axis=1).reset_index()


    def stall(self, re: npt.ArrayLike, n_cl=50, clipre: bool=True) -> pd.Series:
        df = self.lookup(re, cl_or_alpha="sweep", n_cl=n_cl, clipre=clipre)
        df = df.loc[~df.lift_warning.astype(bool)]

        return df.groupby("re").apply(lambda x: x.loc[x.cl.idxmax()], include_groups=False)


    @staticmethod
    def from_files(lft, drg):
        with open(lft, "r") as f:
            lftp = LFTDRGParser(f)
            lft = lftp.read_all()
        with open(drg, "r") as f:
            lftp = LFTDRGParser(f)
            drg = lftp.read_all()
        return UIUCPolars(lft, drg)

    @staticmethod
    def download(airfoil_name: str):
        return UIUCPolars.from_files(*UIUCPolars._get_uiuc_files(airfoil_name))

    @staticmethod
    def local(airfoil_name: str):
        return UIUCPolars(
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


def _list_uiucurl(vol):
    resp = urllib.request.urlopen(
        f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/"
    )
    soup = BeautifulSoup(resp, features="html.parser")

    def isaf(file):
        return ".DRG" in file

    files = [node.get("href") for node in soup.find_all("a")]
    return [f[:-4] for f in files if isaf(f)]


import itertools


def uiuc_airfoils():
    return list(itertools.chain(*[_list_uiucurl(i + 1) for i in range(4)]))


def list_url_files(url, extension):
    resp = urllib.request.urlopen(url)
    soup = BeautifulSoup(resp, features="html.parser")

    def isaf(file):
        return f".{extension}" in file

    files = [node.get("href") for node in soup.find_all("a")]
    return [f[:-4] for f in files if isaf(f)]


if __name__ == "__main__":
    afoil = UIUCPolars.local("CLARKYB")
    print(afoil.lookup(re=10000, cl=0.6))
    pass
#    for afname in uiuc_airfoils():
#        for fi, ld in zip(UIUCPolars._get_uiuc_files(afname), ["LFT", "DRG"]):
#            with open(f"acdesign/data/uiuc/{afname}.{ld}", "w") as fo:
#                with open(fi, "r") as fin:
#                    fo.write(fin.read())
#                    pass
