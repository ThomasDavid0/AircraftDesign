from pathlib import Path

import numpy as np
import pandas as pd

from acdesign.avl.parse_avl_output import (
    parse_stability_derivatives,
    parse_strip_force_df,
    parse_total_forces,
)


def test_parse_strip_forces():
    file = Path("tests/data/strip_forces.out")
    sfdf = parse_strip_force_df(file)
    assert isinstance(sfdf, pd.DataFrame)
    assert len(sfdf) == 200




def test_pase_total_forces():
    file = Path("tests/data/total_forces.out")
    data = parse_total_forces(file)
    assert data["CLtot"] == 0.9


def test_parse_stability_derivatives():
    file = Path("tests/data/stability_derivatives.out")
    data = parse_stability_derivatives(file)
    assert isinstance(data, dict)
    assert len(data)==62