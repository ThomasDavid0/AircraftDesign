import pytest
from geometry import Point
import numpy as np
from acdesign.aircraft.rib import Rib
from acdesign.aircraft.panel import Panel

rib = {
    "airfoil": "a18-il",
    "chord": 0.2,
    "te_thickness": 0.0005,
    "incidence": 1.0
}



def test_parse_rib():
    _rib = Rib.create(**rib)

    #assert _rib.transform.translation == Point(0,0.0, 0.05)
    assert _rib.chord == rib["chord"]
    assert _rib.te_thickness == rib["te_thickness"]
    assert _rib.transform.rotation.to_euler().y == np.radians(rib["incidence"])

panel = {
    "name": "testpanel",
    "acpos": {"x":-200,"y": 100,"z": 0},
    "dihedral": 5.0,
    "incidence": 0.0,
    "symm": True,
    "length": 500,
    "sweep": 200,
    "inbd": {
        "airfoil": "a18-il",
        "chord": 200,
        "te_thickness": 0.0005,
        "incidence": 1.0
    },
    "otbd": {
        "airfoil": "ag16-il",
        "chord": 150,
        "te_thickness": 0.0005,
        "incidence": 0.0
    }
}

def test_parse_panel():
    _panel = Panel.create(**panel)

    assert _panel.symm == True

    assert _panel.transform.translation == Point(-200, 100, 0.0)
    
    assert isinstance(_panel.inbd, Rib)
