import pytest
from acdesign.aircraft import Panel, Rib, Airfoil
from geometry import Transformation, Point, Quaternion, Euler
import numpy as np


@pytest.fixture
def _panel():
    return Panel(
        "testpanel",
        Transformation(
            Point(0.2, 0.1, 0.1),
            Euler(np.radians(-5), 0.0, 0.0)
        ),
        True, 
        Rib.create("e1200-il", .3, Point.zeros(), 0, 0.0004),
        Rib.create("e1200-il", .3, Point(0.2, 0.0, 0.5), 0, 0.0004)
    )


def test_area(_panel):
    assert _panel.area == 0.5*0.3 * 2

def test_semispan(_panel):
    assert _panel.semispan == 0.5

def test_taper_ratio(_panel):
    assert _panel.taper_ratio == 1.0

def test_le_sweep_angle(_panel):
    pytest.approx(_panel.le_sweep_angle, np.arctan2(0.2,0.5)) 


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
