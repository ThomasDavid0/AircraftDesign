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


