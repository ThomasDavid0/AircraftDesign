import urllib.request
from importlib.resources import files
from io import TextIOWrapper
from numbers import Number
from typing import Union
from urllib.error import HTTPError

import numpy as np
import pandas as pd
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

        direc = np.sign(np.gradient(df.Cl)) if len(df) > 1 else np.ones(1)
        ist = len(df) if np.all(direc == 1) else df.loc[direc < 0].iloc[0].name
        arr = np.concatenate([np.ones(ist), -np.ones(len(df) - ist)])
        return df.assign(pre_stall=arr)


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
        self.lift = lift
        self.drag = drag

        self.pslift = self.lift.loc[self.lift.pre_stall == 1]
        self.pslift = self.pslift.assign(
            group=np.cumsum(self.pslift.re.diff() / self.pslift.re > 0.2)
        )
        self.pslift = pd.concat(
            [
                self.pslift.loc[self.pslift.group == 0].assign(re=0),
                self.pslift,
                self.pslift.loc[
                    self.pslift.group == self.pslift.group.unique()[-1]
                ].assign(re=2000000),
            ]
        )

        self.pslift.assign(
            group=np.cumsum(self.pslift.re.diff() / self.pslift.re > 0.2)
        )

        self.alpha_to_cl = linear_or_nearest(
            (self.pslift.re, self.pslift.alpha), self.pslift.Cl
        )
        self.cl_to_alpha = linear_or_nearest(
            (self.pslift.re, self.pslift.Cl), self.pslift.alpha
        )
        self.cl_to_cm = linear_or_nearest(
            (self.pslift.re, self.pslift.Cl), self.pslift.Cm
        )

        self.cl_to_cd = linear_or_nearest((self.drag.re, self.drag.Cl), self.drag.Cd)

    def apply(self, recl: np.ndarray) -> pd.DataFrame:
        alpha, stall = self.cl_to_alpha(recl)

        return pd.DataFrame(
            np.column_stack(
                [
                    recl[:, 0],
                    alpha,
                    recl[:, 1],
                    self.cl_to_cm(recl)[0],
                    self.cl_to_cd(recl)[0],
                    stall,
                ]
            ),
            columns=["re", "alpha", "Cl", "Cm", "Cd", "stall"],
        )

    def lookup(self, re: Union[list, Number], cl: Union[list, Number]) -> pd.DataFrame:
        re = [re] if isinstance(re, Number) else re
        cl = [cl] if isinstance(cl, Number) else cl
        return self.apply(np.column_stack([re, cl]))

    def alookup(
        self, re: Union[list, Number], alpha: Union[list, Number]
    ) -> pd.DataFrame:
        return self.lookup(re, self.alpha_to_cl(re, alpha))

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
