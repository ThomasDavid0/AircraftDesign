
from acdesign.atmosphere import Atmosphere
from acdesign.performance.aero import WingAero
from pytest import fixture, approx
from acdesign.airfoils.polar import UIUCPolars
from acdesign.performance.operating_point import OperatingPoint


@fixture
def clarky():
    return UIUCPolars.local("CLARKYB")


@fixture 
def wing(clarky):
    return WingAero(3, 3 / 15, [clarky],[0, 1])

@fixture
def op():
    return OperatingPoint(Atmosphere.alt(0), 20)

def test_call(wing: WingAero, op: OperatingPoint):
    res = wing(op, 1)

    assert res["Cl"] == approx(1)

def test_wing_stall_cl(wing: WingAero, op):
    sc = wing.stall(op)
    assert sc['Cl'] == approx(1.28, rel=0.01)



def test_wing_stall_cl2(wing: WingAero, op):
    wing = WingAero(3, 3 / 15, [UIUCPolars.local("CLARKYB"),UIUCPolars.local("SA7038")],[0, 0.4, 1])
    op = OperatingPoint(Atmosphere.alt(0), 15)

    stall = wing.stall(op)
    assert stall['cl'] == approx(1.28, rel=0.01)


