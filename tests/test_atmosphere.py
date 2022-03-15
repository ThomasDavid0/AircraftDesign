from pytest import fixture, approx
from acdesign.atmosphere import Atmosphere
import numpy as np
import pandas as pd


def test_resource():
    assert isinstance(Atmosphere.atm, pd.DataFrame)


def test_alt():
    atm = Atmosphere.alt(0)
    assert isinstance(atm, Atmosphere)
    assert atm.T == 288.15

    atm = Atmosphere.alt(250)
    assert atm.T == np.mean([Atmosphere.atm.loc[0,"T"], Atmosphere.atm.loc[500,"T"]])

    assert Atmosphere.alt(0).rho == approx(1.225, 1e-4)