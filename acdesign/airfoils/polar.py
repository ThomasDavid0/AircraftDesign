import numpy as np 
import pandas as pd
from io import TextIOWrapper
from scipy.interpolate import interp2d, griddata
from numbers import Number
from typing import Union
import urllib.request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from pkg_resources import resource_stream, resource_listdir

all_resources = resource_listdir("acdesign", "data")

def getresource(name: str):
    return resource_stream('acdesign', f'data/{name}')


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
            if "Average Reynolds #:" in line.decode():
                re = float(self.f.readline().decode().strip())
                break
        else:
            return None                  

        assert "Number of angles of attack:" in self.f.readline().decode()
        n = int(self.f.readline().decode().strip())

        headings = [h.strip() for h in self.f.readline().decode().strip().split('/')]
        
        rows = [self.f.readline().decode().strip().split() for _ in range(n)]

        if ">>>" in headings[-1]:
            headings = headings[:-1] + [f"scd{i}" for i in range(len(rows[0]) - 3)]

        df = pd.DataFrame(rows, columns = headings).astype("float").assign(re=re)

        direc = np.sign(np.gradient(df.Cl)) if len(df) > 1 else np.ones(1)
        ist = len(df) if np.all(direc==1) else df.loc[direc < 0].iloc[0].name
        arr = np.concatenate([np.ones(ist), -np.ones(len(df)-ist) ])
        return df.assign(pre_stall=arr)


def interpgrid(x,y,z, method="linear"):
    def _interp(tests):
        res = griddata(
            np.column_stack([x,y]), 
            z.to_numpy(), 
            tests,
            method
        )
        nans = np.isnan(res)
        if np.any(nans):

            resnan = griddata(
                np.column_stack([x,y]), 
                z.to_numpy(), 
                tests,
                method="nearest",
            )
            res[nans] = resnan[nans]
        return res

    return _interp


class UIUCPolars:
    def __init__(self, lift: pd.DataFrame, drag: pd.DataFrame):
        self.lift = lift
        self.drag = drag

        self.pslift = self.lift.loc[self.lift.pre_stall==1]
    
        self.alpha_to_cl = interpgrid(self.pslift.re, self.pslift.alpha, self.pslift.Cl)

        self.cl_to_alpha = interpgrid(self.pslift.re, self.pslift.Cl, self.pslift.alpha)
        self.cl_to_cm = interpgrid(self.pslift.re, self.pslift.Cl, self.pslift.Cm)
        self.cl_to_cd = interpgrid(self.drag.re, self.drag.Cl, self.drag.Cd)
    

    def apply(self, recl: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(
            np.column_stack([
                recl[:,0],
                self.cl_to_alpha(recl),
                recl[:,1],
                self.cl_to_cm(recl),
                self.cl_to_cd(recl)
            ]),
            columns=["re", "alpha", "Cl", "Cm", "Cd"]
        )

    def lookup(self, re:Union[list, Number], cl:Union[list, Number]) -> pd.DataFrame:
        re = [re] if isinstance(re, Number) else re
        cl = [cl] if isinstance(cl, Number) else cl        
        return self.apply(np.array([[r, c] for c in cl for r in re]))

    def alookup(self, re: Union[list, Number], alpha:Union[list, Number]) -> pd.DataFrame:
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
            LFTDRGParser(getresource(f"uiuc/{airfoil_name}.LFT")).read_all(), 
            LFTDRGParser(getresource(f"uiuc/{airfoil_name}.DRG")).read_all()
        )
#        return UIUCPolars.from_files(*[f"acdesign/data/uiuc/{airfoil_name}.{ld}" for ld in ["LFT", "DRG"]])

    @staticmethod
    def _get_uiuc_files(airfoil_name):
        for vol in range(1,5):         
            uiucurl = f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/{airfoil_name}"
            try:
                return [urllib.request.urlretrieve(f"{uiucurl}.{ld}")[0] for ld in ["LFT", "DRG"]]
            except HTTPError:
                pass
        else:
            return None


def _list_uiucurl(vol):
    resp = urllib.request.urlopen(f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/")
    soup = BeautifulSoup(resp, features="html.parser")
    def isaf(file):
        return ".DRG" in file

    files = [node.get("href") for node in soup.find_all('a')]
    return [f[:-4] for f in files if isaf(f)]

import itertools

def uiuc_airfoils():
    return list(itertools.chain(*[_list_uiucurl(i+1) for i in range(4)]))


def list_url_files(url, extension):
    resp = urllib.request.urlopen(url)
    soup = BeautifulSoup(resp, features="html.parser")
    def isaf(file):
        return f".{extension}" in file

    files = [node.get("href") for node in soup.find_all('a')]
    return [f[:-4] for f in files if isaf(f)]




if __name__ == '__main__':
    for afname in uiuc_airfoils():
        for fi, ld in zip(UIUCPolars._get_uiuc_files(afname), ["LFT", "DRG"]):
            with open(f"acdesign/data/uiuc/{afname}.{ld}", "w") as fo:
                with open(fi, "r") as fin:
                    fo.write(fin.read())
                    pass