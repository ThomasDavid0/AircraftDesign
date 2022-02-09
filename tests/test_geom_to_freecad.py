import acdesign.cad.geom_to_freecad
import freecad
from geometry import Point, Euler, Quaternion, Transformation
import pytest
import numpy as np


def test_point_to_vector():
    fc_vec = Point(1,2,3).to_vector()
    assert isinstance(fc_vec, freecad.app.Vector)


def test_add_points():
    p = Point(1,2,3)
    vec = p.to_vector()

    assert vec + vec == (p+p).to_vector()


def test_q_to_rotation():
    q = Euler(np.pi/4, 0, 0)
    r = q.to_rotation()
    
    # freecad works in degrees and the euler angles are defined yaw-pitch-roll
    np.testing.assert_array_almost_equal(r.toEuler(), (0,0,45))


def test_t_to_placement():
    t = Transformation(Point(100,200,300), Euler(np.pi/4, 0, 0))
    p = t.to_placement()
    assert p.Base == t.translation.to_vector()
    assert p.Rotation == t.rotation.to_rotation()
    