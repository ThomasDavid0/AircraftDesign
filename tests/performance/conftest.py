from acdesign.performance.operating_point import OperatingPoint
from acdesign.atmosphere import Atmosphere
from pytest import fixture
from acdesign.performance.aero import AircraftAero, WingAero, FuseAero
from acdesign.airfoils.polar import UIUCPolars

@fixture
def op():
    return OperatingPoint(Atmosphere.alt(0), 23)

@fixture
def fd():
    return FuseAero(2, 0.125)

@fixture(scope="session")
def wing():
    return WingAero(
        3.205, 
        0.733561, 
        [
            UIUCPolars.local("CLARKYB"),
            UIUCPolars.local("SA7038")
        ],
        [0, 1/3, 1]
    )



@fixture
def dmodel(wing, fd):
    return AircraftAero(
        wing,
        WingAero(
            0.716584, 
            0.146712, 
            [UIUCPolars.local("E472")],
            [0,1]
        ),
        fd,
        0.02,
        1.3
    )