import pytest
from acdesign.aircraft import Panel, Rib, Airfoil
from geometry import Transformation, Point, Quaternion, Euler
import numpy as np


@pytest.fixture
def _panel():
    return Panel(
        "testpanel",
        Transformation(
            Point(200, 100, 100),
            Euler(np.radians(-5), 0.0, 0.0)
        ),
        True, 
        Rib.create("e1200-il", 300, Point.zeros(), 0, 4),
        Rib.create("e1200-il", 300, Point(200, 500, 0), 0, 4)
    )


def test_area(_panel):
    assert _panel.area == 500.0*300.0 * 2

def test_semispan(_panel):
    assert _panel.semispan == 500

def test_taper_ratio(_panel):
    assert _panel.taper_ratio == 1.0

def test_le_sweep_angle(_panel):
    pytest.approx(_panel.le_sweep_angle, np.arctan2(200,500)) 


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
        "te_thickness": 5,
        "incidence": 1.0
    },
    "otbd": {
        "airfoil": "ag16-il",
        "chord": 150,
        "te_thickness": 5,
        "incidence": 0.0
    }
}


def test_parse_panel():
    _panel = Panel.create(**panel)

    assert _panel.symm == True

    assert _panel.transform.translation == Point(-200, 100, 0.0)
    
    assert isinstance(_panel.inbd, Rib)
