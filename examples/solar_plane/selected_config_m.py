import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px

    from acdesign.airfoils.polar import UIUCPolar
    from acdesign.atmosphere import Atmosphere
    from acdesign.solar_wing import SolarWing

    section = UIUCPolar.local("SG6041")

    atm = Atmosphere.alt(0)
    masses, airspeeds = 4.5, np.linspace(7, 25, 42)

    wing = SolarWing.straight_to_elliptical(19, 18, 2, section)

    wing.data()

    return airspeeds, atm, masses, px, wing


@app.cell
def _(airspeeds, atm, masses, wing):

    results = wing.drag(atm, airspeeds, masses*9.81)

    results.to_csv("solar_plane_results.csv")
    return (results,)


@app.cell
def _(airspeeds, px, results):
    px.line(
    
        x=airspeeds,
        y=results.Cl / (results.Cd + 0.02),
    )

    return


if __name__ == "__main__":
    app.run()
