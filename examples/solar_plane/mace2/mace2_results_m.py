import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    # Import main_wing and aircraft from mace0 module
    #sys.path.insert(0, "examples/solar_plane/mace2")
    import mace2_option1 as option1
    import mace2_option2 as option2
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    from acdesign.airfoils import Airfoil
    from acdesign.atmosphere import Atmosphere
    from acdesign.solar_wing import (  #, assess_solar_performance
        SolarWing,
        assess_solar_performance,
    )



    return assess_solar_performance, go, option1, option2


@app.cell
def _(go, option1, option2):
    import numpy as np

    # Create a single 3D plot
    fig = go.Figure()

    # Add option1 traces (no offset)
    for trace in option1.aircraft.plot().data:
        trace.name = f"Option 1 - {trace.name}" if trace.name else "Option 1"
        trace.showlegend = False
        fig.add_trace(trace)

    # Add option2 traces (offset by 2m in Z)
    for trace in option2.aircraft.plot().data:
        z_offset = np.array(trace.z) + 2.0 if trace.z is not None else None
        trace_copy = go.Scatter3d(
            x=trace.x,
            y=trace.y,
            z=z_offset,
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
        template="simple_white",
        scene=dict(
            xaxis=dict(visible=False, range=[-0.5, 2.5], title="X (m)"),
            yaxis=dict(visible=False, range=[-3, 3], title="Y (m)"),
            zaxis=dict(visible=False, range=[-1, 3], title="Z (m)"),
            aspectmode='data',
            camera=dict(
                eye=dict(x=-1.5, y=-0.3, z=0.8),  # Adjust the camera position for a better view
            
                #projection=dict(type='orthographic')  # Use perspective projection for better depth perception
            ),
            #aspectratio=dict(x=1.0, y=1.0, z=1.0) 
        
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        width=600,
        height=400,
    )

    fig.show()
    return


@app.cell
def _(assess_solar_performance, option1):
    assess_solar_performance(option1.results, option1.aircraft, option1.npanels,2.5, option1.capacity, option1.cells)
    return


@app.cell
def _(assess_solar_performance, option2):
    assess_solar_performance(option2.results, option2.aircraft, option2.npanels,2.5, option2.capacity, option2.cells)
    return


@app.cell
def _(option1, option2):

    option1.main_wing.plot().update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), width=600, height=150).show()
    option2.main_wing.plot().update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), width=800, height=150).show()
    return


@app.cell
def _(go, option1, option2):
    # L/D vs Airspeed plot
    fig_ld = go.Figure()
    fig_ld.add_trace(
        go.Scatter(
            x=option1.results.u,
            y=option1.results.cl / option1.results.cd,
            mode="lines",
            name="Option 1",
        )
    )
    fig_ld.add_trace(
        go.Scatter(
            x=option2.results.u,
            y=option2.results.cl / option2.results.cd,
            mode="lines",
            name="Option 2",
        )
    )
    fig_ld.update_layout(
        template="plotly_white",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="L/D",
        legend=dict(x=0.4, y=0.9, orientation="h"),
        width=600,
        height=400,
        margin=dict(l=50, r=0, t=0, b=50)
    )
    fig_ld
    return


@app.cell
def _(go, option1, option2):


    max_cl = 0.7
    g = 9.81

    fig_power = go.Figure()
    fig_power.add_trace(
        go.Scatter(
            x=option1.results.u,
            y=option1.results.power,
            mode="lines+markers",
            name="Option 1",
        )
    )
    fig_power.add_trace(
        go.Scatter(
            x=option2.results.u,   
            y=option2.results.power,
            mode="lines+markers",
            name="Option 2",
        )
    )
    fig_power.add_hline(
        y=option1.npanels * 2.5,
        line_dash="dot",
        annotation_text=f"Option 1 Solar Available ({option1.npanels} {2.5} W panels)",
        annotation_position="top left",
    )
    fig_power.add_hline(
        y=option2.npanels * 2.5,
        line_dash="dot",
        annotation_text=f"Option 2 Solar Available ({option2.npanels} {2.5} W panels)",
        annotation_position="top left",
    )
    #fig_power.add_vline(
    #    x=u_4000_cl06,
    #    line_dash="dash",
    #    line_color="blue",
    #    annotation=dict(
    #        text=f"4000m Cl={max_cl:.2f} ({u_4000_cl06:.1f} m/s)",
    #        textangle=90
    #    )
    #
    #)
    fig_power.update_layout(
        template="plotly_white",
        xaxis=dict(
            range=[8, 25],
            title="Airspeed (m/s)",
        ),
        yaxis=dict(
            range=[0, 400],
            title="Power (W)",
        ),
        legend=dict(
            x=0.2,
            y=0.9,
            orientation="h",
            bgcolor="rgba(255, 255, 255, 0.5)",
            bordercolor="rgba(0, 0, 0, 0.5)",
        ),
        width=600,
        height=400,
        margin=dict(l=50, r=0, t=0, b=50)
    )
    #fig_power.write_image("examples/solar_plane/mace2/mace2_power_vs_airspeed.svg")
    fig_power
    return


if __name__ == "__main__":
    app.run()
