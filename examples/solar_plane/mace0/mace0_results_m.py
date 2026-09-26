import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    return Path, go, mo, pd


@app.cell
def _(Path, pd):
    # Load the CSV files
    results_sl = pd.read_csv(Path("examples/solar_plane/mace0/airspeed_sweep_sl.csv"))
    results_9000 = pd.read_csv(Path("examples/solar_plane/mace0/airspeed_sweep_9000.csv"))
    return results_9000, results_sl


@app.cell
def _(go, results_9000, results_sl):
    # L/D vs Airspeed plot
    fig_ld = go.Figure()
    fig_ld.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.cl / results_sl.cd,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig_ld.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.cl / results_9000.cd,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig_ld.update_layout(
        template="plotly_white",
        title="MACE0 L/D vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="L/D",
    )
    fig_ld
    return


@app.cell
def _(go, results_9000, results_sl):
    import sys
    from acdesign.airfoils import Airfoil
    from acdesign.solar_wing import SolarWing
    
    # Import main_wing from mace0 module
    sys.path.insert(0, "examples/solar_plane/mace0")
    from mace0 import main_wing

    fig_power = go.Figure()
    fig_power.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.power,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig_power.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.power,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig_power.add_hline(
        y=main_wing.npanels * main_wing.cell_power,
        line_dash="dot",
        annotation_text="Available Solar Power",
        annotation_position="top left",
    )
    fig_power.update_layout(
        template="plotly_white",
        title="MACE0 Power vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="Power (W)",
    )
    fig_power
    return


if __name__ == "__main__":
    app.run()
