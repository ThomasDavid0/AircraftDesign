import pytest
from acdesign.old_aircraft.component_mass import ComponentMass
from geometry import Point, Mass, P0
import numpy as np


def test_combine():
    masses = [
        ComponentMass("test", Point(0,0,0), Mass.point(10)),
        ComponentMass("test", Point(9,9,9), Mass.point(5))
    ]

    mass = ComponentMass.combine(masses)

    assert mass.mass.m[0] == 15
    assert mass.cg == Point(3,3,3)


def test_create_point():
    p = ComponentMass.create("thing", dict(x=0, y=0, z=0), 10, dict(shape="point"))

    assert p.mass.m[0]==10
    np.testing.assert_array_equal(p.mass.matrix()[0], np.zeros((3,3)))