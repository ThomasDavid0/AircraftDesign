from pytest import fixture, approx

from acdesign.airfoils.polar import LFTDRGParser, UIUCPolars, _list_uiucurl, uiuc_airfoils
import numpy as np
import pandas as pd






def test_read_next_re_table_lft():
    with open('tests/airfoils/S1223.LFT', "r") as f:
        lftp = LFTDRGParser(f)
        re = lftp.read_next_re_table()
    assert isinstance(re, pd.DataFrame)
    assert np.all(re.re == 61000)
    assert not np.all(re.pre_stall == 1)


def test_read_next_re_table_drg_single_entry():
    with open('tests/airfoils/CLARKYB.DRG', "r") as f:
        lftp = LFTDRGParser(f)
        [f.readline() for _ in range(48)]
        re = lftp.read_next_re_table()
    assert isinstance(re, pd.DataFrame)
    assert np.all(re.re == 99000)
    assert np.all(re.pre_stall == 1)


def test_read_next_re_table_drg():
    with open('tests/airfoils/S1223.DRG', "r") as f:
        lftp = LFTDRGParser(f)

        re = lftp.read_next_re_table()
    assert isinstance(re, pd.DataFrame)
    assert np.all(re.re == 100600)
    assert np.all(re.pre_stall == 1)



def test_read_all():
    with open('tests/airfoils/S1223.LFT', "r") as f:
        lftp = LFTDRGParser(f)
        res = lftp.read_all()
    
    assert isinstance(res, pd.DataFrame)
    assert np.all(res.columns == ["alpha", "Cl", "Cm", "re", "pre_stall"])


@fixture
def s1223():
    return UIUCPolars.from_files('tests/airfoils/S1223.LFT', 'tests/airfoils/S1223.DRG')

def test_alpha_to_cl(s1223):
    assert s1223.alpha_to_cl([122600, 1.53])[0] == approx(
        s1223.lift.loc[
            np.logical_and(s1223.lift.alpha==1.53, s1223.lift.re==122600), :
        ].Cl.item(),
        1e-2
    )
    assert s1223.alpha_to_cl([122600, np.mean([1.53, 2.57])]) == approx(np.mean([1.204,1.297]), 1e-5)

def test_lookup(s1223):
    df = s1223.lookup(re=[100000, 200000], cl=[0.1,0.2,0.8])
    assert isinstance(df, pd.DataFrame)


def test_download():
    clarky = UIUCPolars.download("CLARKYB")
    assert isinstance(clarky, UIUCPolars)

def test_list_uiuc():
    airfoils = _list_uiucurl(1)
    assert "BE50" in airfoils

def test_uiuc_airfoils():
    assert "CLARKYB" in uiuc_airfoils()
