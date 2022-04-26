from pytest import approx, fixture
from acdesign.aircraft.plane import ConventionalPlane
from acdesign.aircraft.wing import Wing

@fixture
def cplane():
    return ConventionalPlane.parse_json("acdesign/data/buddi_tilt.json")



def test_cplane_wing(cplane):
    assert isinstance(cplane.wing, Wing)
    assert len(cplane.wing.panels) == 2
    




