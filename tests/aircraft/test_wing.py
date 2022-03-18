from acdesign.aircraft import Rib, Panel
from acdesign.aircraft.wing import Wing
from geometry import Point
from .conftest import _panel
import numpy as np
from pytest import approx

ribs = [
    Rib.create("e174-il", 200, Point(0,   0,   0), 1),
    Rib.create("e174-il", 200, Point(0,   80,  0), 1),
    Rib.create("e174-il", 180, Point(20,  180, 0), 1),
    Rib.create("e174-il", 160, Point(40,  400, 0), 1),
    Rib.create("e174-il", 100, Point(100, 800, 0), 1),
]

def test_from_ribs():
    wing = Wing.from_ribs(ribs)
    assert len(wing.panels) == 4
    assert wing.panels[1].transform.translation == Point(0, 80, 0)
    assert wing.panels[1].inbd.transform.translation == Point(0, 0, 0)
    assert wing.panels[1].otbd.transform.translation == Point(20, 100, 0)


def test_S(_panel):
    assert Wing([_panel]).S == 500 * 300

def test_b(_panel):
    assert Wing([_panel]).b == 600

def test_scale():
    wing = Wing.from_ribs(ribs)
    swing = wing.scale(2)
    assert swing.b == wing.b * 2
    assert swing.S == approx((np.sqrt(wing.S) * 2)**2)

def test_mean_chord():
    wing = Wing.from_ribs(ribs)
    assert wing.SMC == 155.5


# TODO need an independent check of these
def test_MAC():
    wing = Wing.from_ribs(ribs)
    assert wing.MAC == approx(118.177920686)

def test_pMAC():
    wing = Wing.from_ribs(ribs)
    assert wing.pMAC.y == approx(234.016613076)
