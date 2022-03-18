
from acdesign.aircraft.airfoil import Airfoil
import numpy as np
import pytest
from geometry import Point


@pytest.fixture
def affile():
    return "tests/data/seligdatfile.txt"


def test_parse_selig(affile):
    af = Airfoil.parse_selig(affile)

    assert isinstance(af.points, Point)


def test_download():
    af = Airfoil.download("b29root-il")
    assert isinstance(af.points, Point)
    assert len(af.points) == 39


@pytest.fixture
def foil(affile):
    return Airfoil.parse_selig(affile)


def test_te_thickness(foil):
    assert foil.te_thickness == 0.007


def test_set_te_thickness(foil):
    nfoil = foil.set_te_thickness(0.1)
    assert nfoil.te_thickness == 0.1


def test_chord(foil):
    assert foil.chord == 1

def test_set_chord(foil):
    nfoil = foil.set_chord(10)
    assert nfoil.chord == 10

def test_thickness(foil):
    assert foil.thickness == 0.07735


def test_le_point(foil):
    assert foil.le_point.x == min(foil.points.x)

def test_top_btm_surface(foil):
    tsurf = foil.top_surface
    bsurf = foil.btm_surface
    assert tsurf[-1] == foil.le_point
    assert bsurf[0] == foil.le_point


def test_mean_camber(foil):
    meanc = foil.mean_camber()
    assert meanc[0] == foil.le_point
    assert meanc[-1] == foil.te_point

    