import pytest
from acdesign.aircraft.mass import Mass
from geometry import Point
import numpy as np


def test_combine():
    masses = [
        Mass("test", Point(0,0,0), 10),
        Mass("test", Point(9,9,9), 5)
    ]

    mass = Mass.combine(masses)

    assert mass.mass == 30
    np.testing.assert_array_almost_equal(mass.cg.to_list(), Point(3,3,3))