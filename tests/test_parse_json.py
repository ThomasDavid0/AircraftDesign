import pytest
from acdesign.parsers.ac_json import parse_rib, parse_panel
from geometry import Point


rib = {
    "span": 0.05,
    "sweep": 0.0,
    "airfoil": "a18-il",
    "chord": 0.2,
    "te_thickness": 0.0005,
    "incidence": 1.0
}




def test_parse_rib():
    _rib = parse_rib(rib)

    assert _rib.transform.translation == Point(0,0.0, 0.05)
    assert _rib.chord == rib["chord"]
    assert _rib.te_thickness == rib["te_thickness"]


panel = {
    "x": 0.2,
    "z": 0.0,
    "dihedral": 5.0,
    "incidence": 0.0,
    "symm": True,
    "inbd": {
        "span": 0.05,
        "sweep": 0.0,
        "airfoil": "a18-il",
        "chord": 0.2,
        "te_thickness": 0.0005,
        "incidence": 1.0
    },
    "otbd": {
        "span": 0.5,
        "sweep": 0.2,
        "airfoil": "ag16-il",
        "chord": 0.15,
        "te_thickness": 0.0005,
        "incidence": 0.0
    }
}

def test_parse_panel():
    _panel = parse_panel(panel)

    assert _panel.symm == True

    assert _panel.transform.translation == Point(0.2, 0.0, 0.0)
    