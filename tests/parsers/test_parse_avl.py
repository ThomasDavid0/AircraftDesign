import pytest
from acdesign.parsers.avl import *
from geometry import Point
from itertools import chain

@pytest.fixture
def avlfile():
    return "tests/data/cold_draft.avl"

@pytest.fixture
def avldata(avlfile):
    return get_avl_data(avlfile)

def test_get_avl_data(avldata):
    assert len(avldata) == 85



def test_getkw():
    assert getkw("SURFACE").word == "SURFACE"
    assert getkw("SURFACE").parms[0].name == "name"
    assert getkw("SURFACE").parms[0].dtype is str



@pytest.fixture
def brokendata(avldata):
    return break_file(avldata)

def test_break_file(brokendata):
    assert len(brokendata[0]) == 6
    assert len(brokendata[1]) == 3
    assert len(brokendata[2]) == 2
    assert all([isinstance(l, str) for l in chain(*brokendata)])



def test_keyword_parse(brokendata):
    res = kwdict["HEADER"].parse(brokendata[0])
    assert isinstance(res, kwdict["HEADER"].NTuple)


@pytest.fixture
def avltuples(brokendata):
    return read_avl(brokendata)


def test_read_avl(avltuples):
    #assert all([isinstance(l, namedtuple) for l in chain(*avltuples)])
    assert avltuples[0].Mach == 0.0
    assert avltuples[0].__class__.__name__ == "HEADER".title()


@pytest.fixture
def tupdict(avltuples):
    return break_tuples(avltuples, ["Surface", "Header", "Body"])

def test_break_tuples(tupdict):
    assert len(tupdict["Header"]) == 1
    assert len(tupdict["Surface"]) == 5


def test_parse_avl_ac(avltuples):
    ac= parse_avl_ac(avltuples)
    assert len(ac.panels) == 12


def test_parse_avl(avlfile):
    ac = parse_avl(avlfile)
    assert isinstance(ac, Plane)