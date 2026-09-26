from pathlib import Path
from typing import Literal, NamedTuple, TextIO

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline, interp1d, make_interp_spline


def get_safe_name(key: str, keys: list[str]) -> str:
    """Get a safe name for a key that is not already in keys."""
    if key not in keys:
        return key
    i = 1
    while f"{key}_{i}" in keys:
        i += 1
    return f"{key}_{i}"




def _parse_avl_dict(f: TextIO, start: str | None, stop="-" * 50):
    data = {}
    start_seen = False or start is None
    for line in f:
        if not start_seen:
            if line.startswith(start):
                start_seen = True
        elif stop in line:
            break
        elif "=" in line:
            entries = line.strip().split()
            if len(entries) < 3:
                continue
            for key, operator, value in zip(
                entries[:-2], entries[1:-1], entries[2:]
            ):
                if operator == "=":
                    try:
                        if key in data:
                            key = get_safe_name(key, list(data.keys()))
                        data[key] = float(value)
                    except ValueError:
                        data[key] = value
    return data

def parse_avl_dict(file: str | Path | TextIO, start: str | None, stop="-" * 50) -> dict:
    if not hasattr(file, "read"):
        with Path(file).open("r") as f:
            return _parse_avl_dict(f, start, stop)
    return _parse_avl_dict(file, start, stop)

def parse_total_forces(file: Path) -> dict:
    """Parse AVL total forces output file into a named tuple."""
    return parse_avl_dict(file, " Vortex Lattice Output -- Total Forces")


def parse_stability_derivatives(file: Path) -> NamedTuple:
    return parse_avl_dict(
        file,
        " Stability-axis derivatives...",
    )


def parse_strip_force_df(file: Path) -> pd.DataFrame:
    """read a strip forces output, return a dataframe"""
    dfs = []
    current_surface = None



    with Path(file).open("r") as f:
        while True:
            while current_surface is None:
                l = f.readline()
                if l == "":
                    return pd.concat(dfs, ignore_index=True)
                if l.startswith("  Surface #"):
                    current_surface = l[17:].strip()
                    
            kwargs = parse_avl_dict(
                f, None, " Strip Forces referred to Strip Area, Chord"
            )

            columns = f.readline().strip().split()
            rows = []
            while True:
                row = f.readline().strip().split()
                if len(row) == len(columns):
                    rows.append([float(v) for v in row])
                else:
                    break
            wing, panel = None, None
            if "panel" in current_surface:
                wing, panel = current_surface.split(" ")[0].split("_panel_", 1)
                panel = int(panel)
            
            dfs.append(
                pd.DataFrame(rows, columns=columns).assign(
                    surface=current_surface, wing=wing, panel=panel, **kwargs
                )
            )
            current_surface = None


def parse_strip_forces(file: Path, b: float) -> pd.DataFrame:
    """Parse AVL strip forces output file into a spline.
    TODO needs to handle each surface separately
    """
    df = parse_strip_force_df(file)
    return make_interp_spline(df.Yle * 2 / b, df.c_cl, k=3)
