from calendar import c
from pytest import fixture, approx

from acdesign.airfoils.polar import LFTDRGParser, UIUCPolar, _list_uiucurl, uiuc_airfoils
import numpy as np
import pandas as pd
import xarray as xr
import geometry as g

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
    return UIUCPolar.local("S1223")

def test_alpha_to_cl(s1223):
    assert s1223.alpha_to_cl.grid(122600, 1.53).values.item() == approx(
        s1223.lift.loc[
            np.logical_and(s1223.lift.alpha==1.53, s1223.lift.re==122600), :
        ].Cl.item(),
        1e-2
    )
    assert s1223.alpha_to_cl.grid(122600, np.mean([1.53, 2.57])).values.item() == approx(np.mean([1.204,1.297]), 1e-5)

    assert not np.isnan(s1223.alpha_to_cl.grid([6e9, 1.53]))[0]


def test_lookup(s1223):
    df = s1223.lookup([100000, 150000, 200000], [0.1,0.2,0.8])


    assert isinstance(df, pd.DataFrame)

def test_lookup_sweep(s1223):
    df = s1223.lookup(150000, "sweep")

    assert isinstance(df, pd.DataFrame)

def test_download():
    clarky = UIUCPolar.local("CLARKYB")
    assert isinstance(clarky, UIUCPolar)

def test_list_uiuc():
    airfoils = _list_uiucurl(1)
    assert "BE50" in airfoils

def test_uiuc_airfoils():
    assert "CLARKYB" in uiuc_airfoils()


def test_get_cd(s1223):
    cds = s1223.cl_to_cd.grid(150000, 0.5)
    assert isinstance(cds, xr.DataArray)
    assert cds.shape == (1,1)
    cds = s1223.cl_to_cd.grid(np.array([100000, 200000]), 0.5)
    assert isinstance(cds, xr.DataArray)
    assert cds.shape == (2,1)
    cds = s1223.cl_to_cd.grid(150000, np.array([0.0, 0.5, 1.0]))
    assert isinstance(cds, xr.DataArray)
    assert cds.shape == (1,3)

    cds = s1223.cl_to_cd.grid(np.linspace(50000, 100000, 4), np.array([0.0, 0.5, 1.0]))
    assert isinstance(cds, xr.DataArray)
    assert cds.shape == (4,3)



def test_get_cd_re_out_of_range(s1223):
    cd1 = s1223.cl_to_cd.grid([5000, s1223.minre], 0.5)
    assert 5000 in cd1.to_dataframe("cd").reset_index().re.to_list()
    
    pass

def test_get_cd_oto(s1223):
    cd1 = s1223.cl_to_cd.oto(np.linspace(50000,100000,4), np.linspace(0,1,4))
    assert cd1.shape == (4,)



def test_load_geometry(s1223: UIUCPolar):
    af = s1223.airfoil()
    assert af.name == "s1223"
    assert isinstance(af.points, g.Point)