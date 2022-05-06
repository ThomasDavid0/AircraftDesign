from acdesign.aircraft import Rib, Panel
from acdesign.aircraft.wing import Wing
from geometry import Point
from .conftest import _panel
import numpy as np
from pytest import approx, fixture


@fixture
def ribs():
    return [
        Rib.create("e174-il", 200, Point(0,   0,   0), 1),
        Rib.create("e174-il", 200, Point(0,   80,  0), 1),
        Rib.create("e174-il", 180, Point(20,  180, 0), 1),
        Rib.create("e174-il", 160, Point(40,  400, 0), 1),
        Rib.create("e174-il", 100, Point(100, 800, 0), 1),
    ]

def test_from_ribs(ribs):
    wing = Wing.from_ribs(ribs)
    assert len(wing.panels) == 4
    assert wing.panels[1].transform.translation == Point(0, 80, 0)
    assert wing.panels[1].inbd.transform.translation == Point(0, 0, 0)
    assert wing.panels[1].otbd.transform.translation == Point(20, 100, 0)


def test_S(_panel):
    assert Wing([_panel]).S == 500 * 300 * 2

def test_b(_panel):
    assert Wing([_panel]).b == 600 * 2

def test_scale(ribs):
    wing = Wing.from_ribs(ribs)
    swing = wing.scale(2)
    assert swing.b == wing.b * 2
    assert swing.S == approx((np.sqrt(wing.S) * 2)**2)

def test_mean_chord(ribs):
    wing = Wing.from_ribs(ribs)
    assert wing.SMC == 155.5


# TODO need an independent check of these
def test_MAC():
    wing = Wing.from_ribs(ribs)
    assert wing.MAC == approx(161.243301178992)

def test_pMAC(ribs):
    wing = Wing.from_ribs(ribs)
    assert wing.pMAC.y[0] == approx(234.016613076)




@fixture
def buddi():
    return Wing.double_taper("wing", 3500, 0.85*1e6, 0.6, 100, ["fx63137-il","fx63137-il","mh32-il","mh32-il"])


def test_double_taper(buddi):
    
    assert buddi.tr == 0.6
    l=0.6

    assert buddi.S == approx(0.85*1e6)
    assert buddi.b == approx(3500) 
    assert buddi.AR == buddi.b**2 / buddi.S
    i=buddi.panels[0]
    o = buddi.panels[1]
    assert buddi.MAC == 2*(i.MAC * i.area + o.MAC * o.area) / buddi.S 

    assert buddi.pMAC.y == (i.pMAC.y * i.area + (o.y + o.pMAC.y) * o.area) / (buddi.S * 0.5)

    assert buddi.panels[0].SMC == approx(286.9760155574762)
    assert buddi.panels[0].root.chord == approx(286.9760155574762)

    #assert buddi.pMAC.x == buddi.pMAC.y * o.le_sweep_distance / (buddi.b * 0.5)


def test_from_panels():
    p1 = Panel.simple("test", 500, 100, Rib.simple("rae101-il", 100, 5), Rib.simple("rae101-il", 50, 5))
    p2 = Panel.simple("test", 500, 100, Rib.simple("rae101-il", 50, 5), Rib.simple("rae101-il", 50, 5))
    w = Wing.from_panels([p1, p2])
    assert w.b == 2000
