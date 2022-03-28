from re import I

from pytest import approx
from acdesign.aircraft import Panel, Rib, Airfoil
from geometry import Transformation, Point, Quaternion, Euler
import numpy as np
from .conftest import _panel


def test_area(_panel):
    assert _panel.area == 500.0*300.0

def test_semispan(_panel):
    assert _panel.semispan == 500

def test_taper_ratio(_panel):
    assert _panel.taper_ratio == 1.0

def test_le_sweep_angle(_panel):
    approx(_panel.le_sweep_angle, np.arctan2(200,500)) 


panel = {
    "name": "testpanel",
    "acpos": {"x":-200,"y": 100,"z": 0},
    "dihedral": 5.0,
    "incidence": 0.0,
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



    assert _panel.transform.translation == Point(-200, 100, 0.0)
    
    assert isinstance(_panel.inbd, Rib)



def test_props():
    p = Panel.create(**panel)

    assert p.area == 175 * 500
    assert p.SMC == np.mean([150,200])
    assert p.taper_ratio == 150 / 200
    assert p.le_sweep_distance == 200
    l = p.taper_ratio
    assert p.MAC == approx((2/3) * p.root.chord * ((1+l+l**2)/(1+l)))

    assert p.pMAC.y == (1/3)*((1+2*l)/(1+l))
    assert p.pMAC.x == p.le_sweep_distance * p.pMAC.y / p.semispan