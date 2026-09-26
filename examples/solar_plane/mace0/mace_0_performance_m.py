import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell
def _(avl_workspace, main_wing, results_9000, results_sl):

    import plotly.graph_objects as go
    import pandas as pd
    from pathlib import Path


    sl = pd.read_csv(Path(avl_workspace, "airspeed_sweep_sl.csv"))
    alt = pd.read_csv(Path(avl_workspace, "airspeed_sweep_9000.csv"))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.cl / results_sl.cd,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.cl / results_9000.cd,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig.update_layout(
        template="plotly_white",
        title="MACE0 L/D vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="L/D",
    )
    fig.show()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_sl.u,
            y=results_sl.power,
            mode="lines+markers",
            name="Sea Level",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_9000.u,
            y=results_9000.power,
            mode="lines+markers",
            name="9000 m",
        )
    )
    fig.add_hline(
        y=main_wing.npanels * main_wing.cell_power,
        line_dash="dot",
        annotation_text="Available Solar Power",
        annotation_position="top left",
    )
    fig.update_layout(
        template="plotly_white",
        title="MACE0 Power vs Airspeed",
        xaxis_title="Airspeed (m/s)",
        yaxis_title="Power (W)",
    )
    fig.show()

    return


if __name__ == "__main__":
    app.run()
