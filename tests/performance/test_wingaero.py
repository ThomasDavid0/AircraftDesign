
from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import WingAero
from pytest import fixture, approx
from acdesign.airfoils.polar import UIUCPolar
from acdesign.performance.operating_point import OperatingPoint
import numpy as np

@fixture
def clarky():
    return UIUCPolar.local("CLARKYB")


@fixture
def s1223():
    return UIUCPolar.local("S1223")


@fixture 
def wing(clarky, s1223):
    return WingAero(3, 1, [clarky],[0, 1])

@fixture
def op():
    return OperatingPoint(Atmosphere.alt(0), 20)

def test_call(wing: WingAero, op: OperatingPoint):

    
    v = np.array([10, 15, 20])
    l = np.array([10, 20])# * 9.81
    ls, vs = np.meshgrid(l, v)
    ls, vs = ls.flatten(), vs.flatten()
    
    res = wing(op.atm, vs, ls)

    np.testing.assert_array_almost_equal(res.lift, ls)

def test_v_min_drag(wing: WingAero, op: OperatingPoint):
    vmin = wing.minimize(lambda row: row.drag, op.atm, np.array([10, 12]) * 9.81)
    assert vmin.fs_v == approx(17.84, rel=0.01)



def test_wing_stall_cl(wing: WingAero, op):
    sc = wing.stall(op)
    assert sc['Cl'] == approx(1.28, rel=0.01)



def test_wing_stall_cl2(wing: WingAero, op):
    wing = WingAero(3, 3 / 15, [UIUCPolar.local("CLARKYB"),UIUCPolar.local("SA7038")],[0, 0.4, 1])
    op = OperatingPoint(Atmosphere.alt(0), 15)

    stall = wing.stall(op)
    assert stall['cl'] == approx(1.28, rel=0.01)


