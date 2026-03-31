import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import pandas as pd

    flapped_results = pd.read_csv("f3a_avl_flapped_results.csv", index_col=0)
    unflapped_results = pd.read_csv("f3a_avl_unflapped_results.csv", index_col=0)
    flapped_results
    return flapped_results, unflapped_results


@app.cell
def _(flapped_results, unflapped_results):
    from turtle import title

    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots   

    _f = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05)

    _x = flapped_results.loc["roll_angle", :]

    _f.add_traces(
        [
            go.Scatter(x=_x, y=flapped_results.loc["CZtot", :], mode="lines", line=dict(dash="solid", color="red"), name="CZtot"),
            go.Scatter(x=_x, y=flapped_results.loc["CYtot", :], mode="lines", line=dict(dash="solid", color="blue"), name="CYtot"),
            go.Scatter(x=_x, y=unflapped_results.loc["CZtot", :], mode="lines", showlegend=False, line=dict(dash="dash", color="red"), name="CZtot"),
            go.Scatter(x=_x, y=unflapped_results.loc["CYtot", :], mode="lines", showlegend=False, line=dict(dash="dash", color="blue"), name="CYtot"),
        ],
        rows=1, cols=1
    )

    _f.add_traces(
        [
            go.Scatter(x=_x, y=flapped_results.loc["Alpha", :], mode="lines", line=dict(dash="solid", color="red"), name="alpha"),
            go.Scatter(x=_x, y=flapped_results.loc["Beta", :], mode="lines", line=dict(dash="solid", color="blue"), name="beta"),
            go.Scatter(x=_x, y=unflapped_results.loc["Alpha", :], mode="lines", showlegend=False, line=dict(dash="dash", color="red"), name="alpha"),
            go.Scatter(x=_x, y=unflapped_results.loc["Beta", :], mode="lines", showlegend=False, line=dict(dash="dash", color="blue"), name="beta"),
        ],
        rows=2, cols=1
    )

    _f.add_traces(
        [
            go.Scatter(x=_x, y=flapped_results.loc["elevator", :], mode="lines", line=dict(dash="solid", color="red"), name="elevator"),
            go.Scatter(x=_x, y=flapped_results.loc["rudder", :], mode="lines", line=dict(dash="solid", color="blue"), name="rudder"),
            go.Scatter(x=_x, y=flapped_results.loc["flap", :], mode="lines", line=dict(dash="solid", color="green"), name="flap"),
            go.Scatter(x=_x, y=flapped_results.loc["sflap", :], mode="lines", line=dict(dash="solid", color="orange"), name="sflap"),
            go.Scatter(x=_x, y=unflapped_results.loc["elevator", :], mode="lines", showlegend=False, line=dict(dash="dash", color="red"), name="elevator"),
            go.Scatter(x=_x, y=unflapped_results.loc["rudder", :], mode="lines", showlegend=False, line=dict(dash="dash", color="blue"), name="rudder"),

        ],
        rows=3, cols=1
    )
    _f.add_traces(
        [
            go.Scatter(x=_x, y=flapped_results.loc["aileron", :], mode="lines", line=dict(dash="solid", color="purple"), name="aileron"),
            go.Scatter(x=_x, y=unflapped_results.loc["aileron", :], mode="lines", showlegend=False, line=dict(dash="dash", color="purple"), name="aileron"),
        ],
        rows=4, cols=1
    )


    _f.update_layout(
        template="plotly_white",
        title="AVL results for a range of roll angles",
        xaxis3_title="Roll angle (degrees)",
        yaxis1_title="Coefficient",
        height=800,
        yaxis2=dict(
            title="Angle of Attack (deg)",
            range=[-2, 2]
        ),
        yaxis3=dict(
            title="Flying Control<br>Deflection (deg)",
            range=[-2, 2]
        ),
        yaxis4=dict(
            title="Correction Control<br>Deflection (deg)",
            range=[-1e-3, 1e-3]   
        )
    )

    _f.write_image("f3a_avl_results.svg")
    _f
    return


if __name__ == "__main__":
    app.run()
