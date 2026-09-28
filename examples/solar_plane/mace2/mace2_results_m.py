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
def _(go, option1, option2):
    import numpy as np

    # Create a single 3D plot
    fig = go.Figure()

    # Add option1 traces (no offset)
    for trace in option1.plot().data:
        trace.name = f"Option 1 - {trace.name}" if trace.name else "Option 1"
        trace.showlegend = False
        fig.add_trace(trace)

    # Add option2 traces (offset by 2m in Z)
    for trace in option2.plot().data:
        trace_copy = go.Scatter3d(
            x=trace.x,
            y=trace.y,
            z=trace.z + 2.0 if trace.z is not None else None,
            mode=trace.mode,
            line=trace.line,
            name=f"Option 2 - {trace.name}" if trace.name else "Option 2",
            showlegend=False,
        )
        fig.add_trace(trace_copy)

    # Add text annotations for each aircraft
    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode="text",
            text=["Option 1"],
            textposition="top center",
            textfont=dict(size=14, color="blue"),
            showlegend=False,
        )
    )
    
    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[2.0],
            mode="text",
            text=["Option 2"],
            textposition="top center",
            textfont=dict(size=14, color="red"),
            showlegend=False,
        )
    )

    # Update layout with appropriate ranges
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-0.5, 2.5], title="X (m)"),
            yaxis=dict(range=[-3, 3], title="Y (m)"),
            zaxis=dict(range=[-1, 3], title="Z (m)"),
            aspectmode='data'
        ),
        title="Aircraft Comparison: Option 1 vs Option 2",
        width=1000,
        height=800,
    )
    
    fig.show()

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
