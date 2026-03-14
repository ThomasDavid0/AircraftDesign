from pytest import approx, fixture, mark
import numpy as np
import geometry as g
from acdesign.aircraft.wing_panel import WingPanel, ControlSurface
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wings import Wings
from acdesign.airfoils.airfoil import Airfoil, InterpolatedAirfoil
from tests.performance.conftest import wing


def test_create_trapezoidal_panel_geometry():
    wingpanel = WingPanel.trapz_crct(1.0, 0.3, 0.3, 0.25)
    assert wingpanel.b == 1.0
    assert wingpanel.S == 0.3
    assert wingpanel.C(0) == 0.3
    assert wingpanel.C(0.5, value=True) == 0.3
    assert wingpanel.C(1) == 0.3
    assert wingpanel.le(0) == 0
    assert wingpanel.le(1) == 0


def test_get_straight_tapered_panel_hinge_location():
    wingpanel = WingPanel.trapz_crct(
        1.0, 0.3, 0.2, 0.25, control=ControlSurface("flap", 0.2, 0.3, 1.0)
    )

    assert wingpanel.get_xhinge(0.5) == approx(0.75)
    assert wingpanel.get_xhinge(0.0) == approx(0.8)
    assert wingpanel.get_xhinge(1.0) == approx(0.7)


@mark.skip(
    reason="This test will only work with nonzero ct, which is not currently implemented"
)
def test_get_elliptical_panel_hinge_location():
    wingpanel = WingPanel.elliptical_cr(
        1.0, 0.3, 0.1, control=ControlSurface("flap", 0.2, 0.3, 1.0)
    )

    assert wingpanel.get_xhinge(0.0) == approx(0.8)
    assert wingpanel.get_xhinge(1.0) == approx(0.7)


def test_get_exact_airfoil_at_spanwise_location():
    panel = WingPanel.trapz_crct(
        1, 0.3, 0.2, airfoils={0: Airfoil.parse_selig("tests/data/goe222.dat")}
    )
    assert panel.get_airfoil(0.5).name == "GOE 222 (MVA H.33) AIRFOIL"


def test_get_interpolated_airfoil_at_spanwise_location():
    panel = WingPanel.trapz_crct(
        1,
        0.3,
        0.2,
        airfoils={
            0: Airfoil.parse_selig("tests/data/rae101.dat"),
            1: Airfoil.parse_selig("tests/data/e168.dat"),
        },
    )
    af = panel.get_airfoil(0.5)
    assert isinstance(af, InterpolatedAirfoil)
    assert af.inbd.name == "RAE 101 AIRFOIL"
    assert af.otbd.name == "E168  (12.45%)"


def test_wingpanel_create_avl_ribs():
    wingpanel = WingPanel.trapz_crct(
        1.0, 0.3, 0.2, 0.25, 
        control=ControlSurface("flap", 0.2, 0.3, 1.0),
        airfoils={
            0: Airfoil.parse_selig("tests/data/rae101.dat"),
            1: Airfoil.parse_selig("tests/data/e168.dat"),
        },
    )

    avl_ribs = wingpanel.create_avl_ribs()

    assert sum(np.array(avl_ribs) == "SECTION") == 2
    

@fixture
def dtwing():
    return Wing(
        "test_wing",
        g.P0(),
        [
            WingPanel.trapz_crct(1.0, 0.3, 0.3, 0.25),
            WingPanel.trapz_crct(1.0, 0.3, 0.2, 0.25),
        ],
    )


def test_retrieves_the_correct_panel_and_spanwise_location(dtwing: Wing):
    id, yloc = dtwing.get_panel(0.25)
    assert id == 0
    assert yloc == 0.5

    id, yloc = dtwing.get_panel(0.5)
    assert id == 0
    assert yloc == 1.0

    id, yloc = dtwing.get_panel(0.5, otbd=True)
    assert id == 1
    assert yloc == 0.0

    results = dtwing.get_panel([0, 0.5, 1.0])
    assert results == [(0, 0.0), (0, 1.0), (1, 1.0)]


def test_gets_chord_at_spanwise_location(dtwing: Wing):
    assert dtwing.C(0) == 0.3
    assert dtwing.C([0, 0.5, 1.0]) == [0.3, 0.3, 0.2]
    assert dtwing.C([0, 0.5, 1.0]) == [0.3, 0.3, 0.2]


@fixture
def stepwing():
    return Wing(
        "test_wing",
        g.P0(),
        [
            WingPanel.trapz_crct(1.0, 0.3, 0.3, 0.25),
            WingPanel.trapz_crct(1.0, 0.2, 0.2, 0.25),
        ],
    )


def test_gets_chord_at_spanwise_location_stepped(stepwing: Wing):
    assert stepwing.C(0.5) == 0.3

    assert stepwing.C(0.5, otbd=True) == 0.2

@fixture
def neg_tr_panel():
    return WingPanel.trapz_crct(1.0, 0.2, 0.3, 1.00, control=ControlSurface("flap", 0.2, 0.3, -1.0))

def test_neg_tr_tip_le_is_neg_x(neg_tr_panel: WingPanel):
    assert neg_tr_panel.le(1.0) == approx(-0.1)


@fixture
def fullwing():
    return Wing(
        "test_wing",
        g.P0(),
        [
            WingPanel.trapz_crct(1.0, 0.2, 0.3, 1.00),
            WingPanel.trapz_crct(1.0, 0.3, 0.3, 1.00),
            WingPanel.trapz_crct(1.0, 0.3, 0.2, 1.00),
        ],
    )

def test_panel_le_points(fullwing: Wing):
    assert fullwing.le(0) == 0
    assert fullwing.le(0.5) == approx(-0.1)
    assert fullwing.le(1.0) == 0