from pytest import approx, fixture
from acdesign.aircraft.plane import ConventionalPlane
from acdesign.aircraft.wing import Wing
from importlib.resources import files
@fixture
def cplane():
    return ConventionalPlane.parse_json((files("data") / "buddi_tilt.json"))



def test_cplane_wing(cplane):
    assert isinstance(cplane.wing, Wing)
    assert len(cplane.wing.panels) == 2
    




