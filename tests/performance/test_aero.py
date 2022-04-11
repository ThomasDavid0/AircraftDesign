
from acdesign.airfoils.polar import UIUCPolars
from pytest import fixture, approx
import numpy as np
import pandas as pd
from .conftest import op, fd, wing, dmodel





def test_fuse_drag(op, fd):
    f = fd(op, 0)
    
    assert f["S"] == approx(0.785398,1e-4)
    assert f["re"]==approx(3096098.6, 1)
    assert f["Cd"]==approx(0.00365, 1e-3)

@fixture
def w(op, wing):
    return wing(op, 0.5)

def test_wing_drag_re(w):
    assert w["re"] == approx(354318,1)
    
def test_wing_drag_coeffs(w):
    assert isinstance(w, dict)
    assert "Cl" in w


def test_get_moment(op, dmodel):
    moment = dmodel.get_moment(op, 10, 0)
    assert isinstance(moment, float)
    
def test_cd(op, dmodel):
    df = dmodel.trim(op, 10)
    assert df.gCd.to_list() == approx([0.008256402853323611, 0.004165965541408166, 0.003907806637803323])




def test_quick_trim(op, dmodel):
    df = dmodel.trim(op, 10)
    df2 = dmodel.quick_trim(op, 10)

    pass