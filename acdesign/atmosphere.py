import numpy as np
import pandas as pd
from pkg_resources import resource_stream
from io import StringIO




class Atmosphere:
    atm = pd.read_csv(StringIO(resource_stream(__name__,'data/atmosphere.csv').read().decode())).astype(float).set_index("h")
    R = 287.058
    GAMMA = 1.4

    def __init__(self, T , p, v, k, c):
        self.T = T
        self.p = p
        self.v = v
        self.k = k
        self.c = c
        self.rho = self.p / (Atmosphere.R * self.T)
    
    @staticmethod
    def alt(h):
        try:
            row=Atmosphere.atm.loc[h]
        except KeyError:
            
            temp = Atmosphere.atm.append(pd.Series(index=Atmosphere.atm.columns, name=h))
            row = temp.interpolate(method="values", axis=0).loc[h]       
        return Atmosphere(row["T"], row.p * 1e5, row.v, row.k, row.c)

