
from acdesign.aircraft.airfoil import Airfoil
import numpy as np
import pytest
from geometry import Points


@pytest.fixture
def affile():
    return "tests/seligdatfile.txt"


def test_parse_selig(affile):
    af = Airfoil.parse_selig(affile)

    assert isinstance(af.points, Points)


def test_download():
    af = Airfoil.download("b29root-il")
    assert isinstance(af.points, Points)
    assert af.points.count == 39


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
