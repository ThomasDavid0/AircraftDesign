from pathlib import Path
from typing import Literal, NamedTuple
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, CubicSpline, make_interp_spline


def parse_strip_force_df(file: Path): 
    """read a strip forces output, return a dataframe"""
    with Path(file).open("r") as f:
        while not f.readline().startswith(" Strip Forces referred to Strip Area, Chord"):
            pass
        columns = f.readline().strip().split()
        rows = []
        while True:
            row = f.readline().strip().split()
            if len(row)==len(columns):
                rows.append([float(v) for v in row])
            else:
                break
    df = pd.DataFrame(rows, columns=columns)
    return df


def parse_strip_forces(file: Path, b: float) -> pd.DataFrame:
    """Parse AVL strip forces output file into a spline."""
    df = parse_strip_force_df(file)
    return make_interp_spline(df.Yle * 2 / b, df.c_cl, k=3)


def parse_total_forces(file: Path) -> NamedTuple:
    """Parse AVL total forces output file into a named tuple."""
    with Path(file).open("r") as f:

        data = {}
        for line in f.readlines():
            line = line.strip(" -")
            if line == "":
                continue
            if "=" not in line:
                continue
            
            entries = line.strip().split()
            if len(entries) < 3:
                continue
            for key, operator, value in zip(entries[:-2], entries[1:-1], entries[2:]):
                if operator == "=":
                    try:
                        data[key] = float(value)
                    except ValueError:  
                        data[key] = value
            #lines.append(f.readline().strip())
    return data