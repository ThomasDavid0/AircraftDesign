
from acdesign.airfoils.polar import UIUCPolar
from acdesign.performance.aero import WingAero, FuseAero, AircraftAero
from acdesign.atmosphere import Atmosphere

from pytest import fixture, approx
import numpy as np
import pandas as pd

from .conftest import op, fd, wing, dmodel


def test_fuse_drag(op, fd):
    f = fd(op, 0)
    
    assert f["S"] == approx(0.785398,1e-4)
    assert f["re"]==approx(3096098.6, 1)
    assert f["Cd"]==approx(0.00365, 1e-3)


@fixture
def plane():
    b = 2
    smc = 0.2
    S = b * smc
    clarky = UIUCPolar.local("CLARKYB")
    sa7038 = UIUCPolar.local("SA7038")
    e472 = UIUCPolar.local("E472")
    fus_length = 1
    return AircraftAero(
        WingAero(b, S, [clarky, sa7038], [0, 0.4, 1]),
        WingAero(b * 0.25, S * 0.2, [e472], [0, 1]),
        WingAero(b * 0.15, S * 0.1, [e472], [0, 1]),
        FuseAero(fus_length, 0.05),
        0.02,
        fus_length * 0.75,
    )

def test_trim(plane: AircraftAero):
    atm = Atmosphere.alt(0)
    v = 20
    lift = 5*9.81

    res = plane.trim(atm, v, lift)
    assert (res.lift_tail + res.lift_wing).iloc[0] == approx(lift, rel=0.01)
    

    