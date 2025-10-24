import pytest
from acdesign.aircraft.plane import Plane
from acdesign.xflr.parse import parse_xflr_plane, parse_xflr_wing
import xml.etree.ElementTree as ET
from geometry import Point

pytest.skip(allow_module_level=True)


def test_parse_xflr_plane():
    plane = parse_xflr_plane("tests/plane_xflr.xml")
    assert plane.name == "plane_test"



def test_parse_xflr_wing():
    rt = ET.parse("tests/plane_xflr.xml").getroot()

    wingxml = rt.find("Plane").findall("wing")[0]
    wing = parse_xflr_wing(wingxml)
    assert wing.name == "Main Wing"
    assert wing.position == Point.zeros()
    assert wing.symmetry == True