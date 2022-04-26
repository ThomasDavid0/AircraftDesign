from this import d
import pytest
from geometry import Transformation, Point, Euler
import numpy as np
from acdesign.avl.dump import *
from acdesign.avl.keywords import kwdict, kw4dict

@pytest.fixture
def _panel():
    return Panel(
        "testpanel",
        Transformation.build(
            Point(-200, 100, -100),
            Euler(np.radians(-5), 0.0, 0.0)
        ),
        [Rib.create("e1200-il", 300, Point.zeros(), 0, 4),
        Rib.create("e1200-il", 300, Point(200, 500, 0), 0, 4)]
    )

def test_keyword_dump():
    tup = kwdict["SECTION"].create(200,50,0,100, 0)
    out = kwdict["SECTION"].dump(tup)

    assert len(out) == 2
    assert out[0]=="SECTION"
    assert out[1] =="200.000 50.000 0.000 100.000 0.000"



def test_rib_dump_avl():
    rib = Rib.create("e168-il", 100, Point(200, 50, 0), 5.0, 5.0)
    lines = rib_dump_avl(rib)

    assert lines[0] == "SECTION"
    assert lines[1] == "200.000 50.000 0.000 100.000 5.000"
    

def test_panel_dump_avl(_panel):
    lines = panel_dump_avl(_panel)
    assert lines[0] == "SURFACE"

    assert lines[1] == _panel.name
    assert lines[2] == "12 1.000"
    assert lines[3] == "SECTION"
    assert lines[4] == "200.000 100.000 100.000 300.000 4.000"
    assert lines[5] == "SECTION"
    assert lines[6] == "400.000 600.000 100.000 300.000 4.000"


