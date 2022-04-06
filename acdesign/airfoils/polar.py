import numpy as np 
import pandas as pd
from io import TextIOWrapper
from scipy.interpolate import interp2d
from numbers import Number
from typing import Union
import urllib.request
from urllib.error import HTTPError
from bs4 import BeautifulSoup


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

        headings = [h.strip() for h in self.f.readline().strip().split('/')]
        
        rows = [self.f.readline().strip().split() for _ in range(n)]

        if ">>>" in headings[-1]:
            headings = headings[:-1] + [f"scd{i}" for i in range(len(rows[0]) - 3)]

        df = pd.DataFrame(rows, columns = headings).astype("float").assign(re=re)
        if len(df) > 1:
            return df.assign(direc = np.sign(np.gradient(df.alpha)))
        else:
            return df.assign(direc=1)



class UIUCPolars:
    def __init__(self, lift: pd.DataFrame, drag: pd.DataFrame):
        self.lift = lift
        self.drag = drag

        self.pslift = self.lift.loc[self.lift.direc==1]
        
        self.alpha_to_cl = interp2d(self.pslift.re, self.pslift.alpha, self.pslift.Cl)

        self.cl_to_alpha = interp2d(self.pslift.re, self.pslift.Cl, self.pslift.alpha)
        self.cl_to_cm = interp2d(self.pslift.re, self.pslift.Cl, self.pslift.Cm)
        self.cl_to_cd = interp2d(self.drag.re, self.drag.Cl, self.drag.Cd)
        
    def lookup(self, re:Union[list, Number], cl:Union[list, Number]) -> pd.DataFrame:
        re = [re] if isinstance(re, Number) else re
        cl = [cl] if isinstance(cl, Number) else cl

        tests = np.array([[r, c] for c in cl for r in re])

        return pd.DataFrame(
            np.column_stack([
                tests[:,0],
                [r for c in self.cl_to_alpha(re, cl) for r in c],
                tests[:,1],
                [r for c in self.cl_to_cm(re, cl) for r in c],
                [r for c in self.cl_to_cd(re, cl) for r in c]
            ]),
            columns=["re", "alpha", "Cl", "Cm", "Cd"]
        )

    def alookup(self, re: Union[list, Number], alpha:Union[list, Number]) -> pd.DataFrame:
        return self.lookup(re, self.alpha_to_cl(re, alpha))
        

    def from_files(lft, drg):
        with open(lft, "r") as f:
            lftp = LFTDRGParser(f)
            lft = lftp.read_all()
        with open(drg, "r") as f:
            lftp = LFTDRGParser(f)
            drg = lftp.read_all()
        return UIUCPolars(lft, drg)


    def download(airfoil_name: str):
        for vol in range(1,5):         
            uiucurl = f"https://m-selig.ae.illinois.edu/pd/pub/lsat/vol{vol}/{airfoil_name}"
            try:
                return UIUCPolars.from_files(
                    *[urllib.request.urlretrieve(f"{uiucurl}.{ld}")[0] for ld in ["LFT", "DRG"]]
                )
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
