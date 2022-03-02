import pytest


from acdesign.avl.keywords import _read_kwordfile, _parse_kwfdata, kwfile, KeyWord, kwdict, get_dtype


def test_read_kwordfile():
    keydata = _read_kwordfile(kwfile)
    assert isinstance(keydata[0], tuple)
    assert len(keydata) == 21


@pytest.fixture
def kwfdata():
    return _read_kwordfile(kwfile)

def test_parse_kwdata(kwfdata):
    kw = KeyWord(*_parse_kwfdata(kwfdata[0]))
    assert isinstance(kw, KeyWord)


@pytest.fixture
def all_kwords(kwfdata):
    return [KeyWord(*_parse_kwfdata(kwfd)) for kwfd in kwfdata]



def test_get_dtype():
    assert get_dtype("0.0") is float
    assert get_dtype("0") is int
    assert get_dtype("sdsdv") is str