from acdesign.avl.parse_avl_output import parse_strip_force_df, parse_strip_forces, parse_total_forces, parse_stability_derivatives
from pathlib import Path    
import numpy as np
import pandas as pd


def test_parse_strip_forces():
    file = Path("tests/data/strip_forces.out")
    df = parse_strip_force_df(file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 50

    sload = parse_strip_forces(file, b=4.5)
    ys = np.linspace(0, 1, 10)
    loads = sload(ys)
    assert len(loads) == 10
    test_vals = sload(df.Yle.values * 2 / 4.5)
    loads = df.c_cl / df.c_cl.mean()
    np.testing.assert_allclose(test_vals, loads)


def test_pase_total_forces():
    file = Path("tests/data/total_forces.out")
    data = parse_total_forces(file)
    assert data["CLtot"] == 0.9


def test_parse_stability_derivatives():
    file = Path("tests/data/stability_derivatives.out")
    data = pd.Series(parse_stability_derivatives(file))
    data.index.name = "name"
    data.name = "value" 

    validation_data = pd.read_csv(Path("tests/data/parsed_st_derivatives.csv"), index_col=0).value

    pd.testing.assert_series_equal(data, validation_data)
