
import pytest
from acdesign.aircraft import Panel, Rib
from geometry import Transformation, Point, Euler
import numpy as np


@pytest.fixture
def _panel():
    return Panel(
        "testpanel",
        Transformation.build(
            Point(200, 100, 100),
            Euler(np.radians(-5), 0.0, 0.0)
        ),
        [Rib.create("e1200-il", 300, Point.zeros(), 0, 4),
        Rib.create("e1200-il", 300, Point(200, 500, 0), 0, 4)]
    )