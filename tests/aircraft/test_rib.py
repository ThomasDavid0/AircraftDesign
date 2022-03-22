from pytest import fixture, approx
from geometry import Point
import numpy as np
from acdesign.aircraft.rib import Rib
from acdesign.aircraft.panel import Panel

_rib = {
    "airfoil": "a18-il",
    "chord": 0.2,
    "te_thickness": 0.0005,
    "incidence": 5.0
}



@fixture
def rib():
    return Rib.create(**_rib)

def test_create_rib(rib):
    

    #assert _rib.transform.translation == Point(0,0.0, 0.05)
    assert rib.chord == _rib["chord"]
    assert rib.te_thickness == _rib["te_thickness"]
    assert rib.transform.rotation.to_euler().z == np.radians(_rib["incidence"])

