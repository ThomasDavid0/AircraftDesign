import pytest
from acdesign.parsers.avl import *
from geometry import Point


@pytest.fixture
def avlfile():
    return "tests/data/cold_draft.avl"

@pytest.fixture
def avldata(avlfile):
    return get_avl_data(avlfile)

def test_get_avl_data(avldata):
    assert len(avldata) == 84

def test_parse_header(avldata):
    headdata = parse_header(avldata[1:5])
    assert isinstance(headdata["momref"], Point)

def test_break_file(avldata):
    case, header, surfaces = break_file(avldata)
    assert case == "Cold Draft"
    assert len(header) == 4
    assert len(surfaces) == 5