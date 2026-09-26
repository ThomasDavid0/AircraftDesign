import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    return Path, go, pd


@app.cell
def _(Path, pd):
    # Load the CSV files
    results_sl = pd.read_csv(Path("examples/solar_plane/mace0/airspeed_sweep_sl.csv"))
    results_9000 = pd.read_csv(Path("examples/solar_plane/mace0/airspeed_sweep_9000.csv"))
    return results_9000, results_sl


@app.cell
def _(results_sl):
    results_sl
    return


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
    from acdesign.atmosphere import Atmosphere

    # Import main_wing and aircraft from mace0 module
    sys.path.insert(0, "examples/solar_plane/mace0")
    from mace0 import main_wing, aircraft

    # Calculate airspeed for Cl = 0.6 at both altitudes
    # L = 0.5 * rho * V^2 * S * Cl, where L = m * g
    # V = sqrt(2 * m * g / (rho * S * Cl))
    target_cl = 0.6
    g = 9.81
    
    atm_sl = Atmosphere.alt(0)
    atm_9000 = Atmosphere.alt(9000)
    
    # V = sqrt(2 * L / (rho * S * Cl)) = sqrt(2 * m * g / (rho * S * Cl))
    u_sl_cl06 = (2 * aircraft.mass.m * g / (atm_sl.rho * aircraft.S * target_cl)) ** 0.5
    u_9000_cl06 = (2 * aircraft.mass.m * g / (atm_9000.rho * aircraft.S * target_cl)) ** 0.5

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
    fig_power.add_vline(
        x=u_sl_cl06,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Cl=0.6 @ SL ({u_sl_cl06:.1f} m/s)",
        annotation_position="top",
    )
    fig_power.add_vline(
        x=u_9000_cl06,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Cl=0.6 @ 9000m ({u_9000_cl06:.1f} m/s)",
        annotation_position="top",
    )
    fig_power.update_layout(
        template="plotly_white",
        title="MACE0 Power vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="Power (W)",
    )
    fig_power
    return Airfoil, Atmosphere, SolarWing, aircraft, atm_9000, atm_sl, fig_power, g, main_wing, sys, target_cl, u_9000_cl06, u_sl_cl06


if __name__ == "__main__":
    app.run()
