import freecad
import pytest
from acdesign.cad.create import create_plane
from acdesign.parsers.ac_json import parse_plane
from acdesign.aircraft.plane import Plane



@pytest.fixture
def plane():
    return parse_plane("tests/aircraft.json")


@pytest.fixture
def create_doc():
    pass


def test_create_plane(plane):
    doc = create_plane(plane,"/home/tom/projects/f3a_design/test2.FCStd")
    assert isinstance(doc, float)