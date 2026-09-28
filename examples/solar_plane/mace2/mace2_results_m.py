import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    # Import main_wing and aircraft from mace0 module
    #sys.path.insert(0, "examples/solar_plane/mace2")
    from mace2_option1 import aircraft as option1
    from mace2_option1 import npanels as option1_npanels
    from mace2_option1 import results as option1_results
    from mace2_option2 import aircraft as option2
    from mace2_option2 import npanels as option2_npanels
    from mace2_option2 import results as option2_results

    from acdesign.airfoils import Airfoil
    from acdesign.atmosphere import Atmosphere
    from acdesign.solar_wing import (  #, assess_solar_performance
            SolarWing,
            assess_solar_performance,
    )



    return Atmosphere, Path, go, option1, option2, pd


@app.cell
def _(option1, option2):
    from plotly.subplots import make_subplots
    import numpy as np
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Option 1", "Option 2"),
        horizontal_spacing=0.1,
        specs=[[{"type": "scatter3d"}, {"type": "scatter3d"}]]
    )

    fig.add_traces(option1.plot().data, rows=1, cols=1)
    fig.add_traces(option2.plot().data, rows=1, cols=2)
    
    # Calculate combined ranges for all axes
    all_x = []
    all_y = []
    all_z = []
    
    for trace in fig.data:
        if hasattr(trace, 'x') and trace.x is not None:
            all_x.extend([v for v in trace.x if v is not None])
        if hasattr(trace, 'y') and trace.y is not None:
            all_y.extend([v for v in trace.y if v is not None])
        if hasattr(trace, 'z') and trace.z is not None:
            all_z.extend([v for v in trace.z if v is not None])
    
    x_range = [min(all_x), max(all_x)] if all_x else [0, 1]
    y_range = [min(all_y), max(all_y)] if all_y else [0, 1]
    z_range = [min(all_z), max(all_z)] if all_z else [0, 1]
    
    # Update both subplots with identical ranges and equal aspect ratio
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode='data'
        ),
        scene2=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode='data'
        )
    )
    
    return


@app.cell
def _(aileron_w, flap_w, gap, main_wing):
    main_wing.plot(
            flap_w=flap_w,
            aileron_w=aileron_w,
            gap=gap,
        ).update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), width=800, height=300).show()
    return


@app.cell
def _(elevator_w, gap, hstab):
    hstab.plot(flap_w=elevator_w, aileron_w=elevator_w, gap=gap).update_layout(template="plotly_white", margin=dict(l=50, r=50, t=0, b=0), width=800, height=300).show()
    return


@app.cell
def _(hstab, main_wing):
    npanels = main_wing.npanels + hstab.npanels
    print(
        f"Total number of panels: {npanels} (wing: {main_wing.npanels}, hstab: {hstab.npanels})"
    )
    return (npanels,)


@app.cell
def _(Path, pd):
    # Load the CSV files
    results_4000 = pd.read_csv(Path("examples/solar_plane/mace2/airspeed_sweep_4000.csv"))
    results_6000 = pd.read_csv(Path("examples/solar_plane/mace2/airspeed_sweep_6000.csv"))
    return results_4000, results_6000


@app.cell
def _(results_4000):
    results_4000
    return


@app.cell
def _(go, results_4000, results_6000):
    # L/D vs Airspeed plot
    fig_ld = go.Figure()
    fig_ld.add_trace(
        go.Scatter(
            x=results_4000.u,
            y=results_4000.cl / results_4000.cd,
            mode="lines+markers",
            name="4000 m",
        )
    )
    fig_ld.add_trace(
        go.Scatter(
            x=results_6000.u,
            y=results_6000.cl / results_6000.cd,
            mode="lines+markers",
            name="6000 m",
        )
    )
    fig_ld.update_layout(
        template="plotly_white",
        title="MACE 2 L/D vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="L/D",
    )
    fig_ld
    return


@app.cell
def _(
    Atmosphere,
    aircraft,
    go,
    hstab,
    main_wing,
    npanels,
    results_4000,
    results_6000,
):


    max_cl = 0.7
    g = 9.81

    atm_4000 = Atmosphere.alt(4000)
    atm_6000 = Atmosphere.alt(6000)

    # V = sqrt(2 * L / (rho * S * Cl)) = sqrt(2 * m * g / (rho * S * Cl))
    u_4000_cl06 = (2 * aircraft.mass.m[0] * g / (atm_4000.rho * aircraft.S * max_cl)) ** 0.5
    u_6000_cl06 = (2 * aircraft.mass.m[0] * g / (atm_6000.rho * aircraft.S * max_cl)) ** 0.5

    fig_power = go.Figure()
    fig_power.add_trace(
        go.Scatter(
            x=results_4000.u,
            y=results_4000.power,
            mode="lines+markers",
            name="4000 m",
        )
    )
    fig_power.add_trace(
        go.Scatter(
            x=results_6000.u,   
            y=results_6000.power,
            mode="lines+markers",
            name="6000 m",
        )
    )
    fig_power.add_hline(
        y=main_wing.npanels * main_wing.cell_power + hstab.npanels * hstab.cell_power,
        line_dash="dot",
        annotation_text=f"Available Solar Power ({npanels} {main_wing.cell_power} W panels)",
        annotation_position="top right",
    )
    fig_power.add_vline(
        x=u_4000_cl06,
        line_dash="dash",
        line_color="blue",
        annotation=dict(
            text=f"4000m Cl={max_cl:.2f} ({u_4000_cl06:.1f} m/s)",
            textangle=90
        )

    )
    fig_power.update_layout(
        template="plotly_white",
        title="MACE 2 Power vs Airspeed",
        xaxis=dict(
            range=[8, 30],
            title="Airspeed (m/s)",
        ),
        yaxis=dict(
            range=[0, 600],
            title="Power (W)",
        ),
        legend=dict(
            x=0.32,
            y=1.2,
            orientation="h",
            bgcolor="rgba(255, 255, 255, 0.5)",
            bordercolor="rgba(0, 0, 0, 0.5)",
        ),
    )
    #fig_power.write_image("examples/solar_plane/mace2/mace2_power_vs_airspeed.svg")
    fig_power
    return


if __name__ == "__main__":
    app.run()
