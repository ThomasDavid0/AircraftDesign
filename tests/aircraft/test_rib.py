import pytest
from geometry import Point
import numpy as np
from acdesign.aircraft.rib import Rib
from acdesign.aircraft.panel import Panel

rib = {
    "airfoil": "a18-il",
    "chord": 0.2,
    "te_thickness": 0.0005,
    "incidence": 5.0
}



def test_create_rib():
    _rib = Rib.create(**rib)

    #assert _rib.transform.translation == Point(0,0.0, 0.05)
    assert _rib.chord == rib["chord"]
    assert _rib.te_thickness == rib["te_thickness"]
    assert _rib.transform.rotation.to_euler().z == np.radians(rib["incidence"])
