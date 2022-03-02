from this import d
import pytest

from acdesign.avl.dump import *
from acdesign.avl.keywords import kwdict, kw4dict


def test_keyword_dump():
    tup = kwdict["SECTION"].create(200,50,0,100, 0)
    out = kwdict["SECTION"].dump(tup)

    assert len(out) == 2
    assert out[0]=="SECTION"
    assert out[1] =="200.000 50.000 0.000 100.000 0.000"

