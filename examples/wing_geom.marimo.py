import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    from acdesign.aircraft.wing_panel import WingPanel, ControlSurface
    import numpy as np
    from acdesign.airfoils.airfoil import Airfoil
    from acdesign.aircraft.wing import Wing
    import geometry as g


    panel = WingPanel.trapz_crct(
        1.0, 
        0.3, 
        0.1, 
        dihedral=np.radians(5), 
        ribs=[0,0.2,0.4,0.6,0.8,1.0],
        airfoils={0: Airfoil.download("clarky"), 1: Airfoil.download("e230")},
        control=ControlSurface("flap", 0.2, 0.3, 1.0)
    )

    _f = panel.plot_planform()
    _f.update_layout(
        template="plotly_white", 
        margin=dict(l=10, r=10, t=10, b=10), 
        width=600, height=300
    )
    return Airfoil, Wing, WingPanel, g, np, panel


@app.cell
def _(panel):
    _f = panel.plot_3d()
    _f.update_layout(
        template="plotly_white", 
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(camera=dict(
            eye=dict(x=1.5, y=-1.5, z=-1.25),
            up=dict(x=0, y=0, z=-1),
        )),
        width=600, height=300
    )
    return


@app.cell
def _(Airfoil, Wing, WingPanel, g, np):



    _wing = Wing("test_wing", g.P0(), [
        WingPanel.trapz_crct(
            1.0, 
            0.5, 
            0.4, 
            dihedral=np.radians(-5),
            airfoils={0:Airfoil.download("clarky")}
        ),
        WingPanel.trapz_crct(
            0.5, 
            0.4, 
            0.3, 
            zerosweep=2,
            dihedral=np.radians(10),
            airfoils={0:Airfoil.download("clarky")}
        )
    ])

    _f = _wing.plot()
    _f.update_layout(
        template="plotly_white", 
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(camera=dict(
            eye=dict(x=1.5, y=-1.5, z=-1.25),
            up=dict(x=0, y=0, z=-1),
        )),
        width=600, height=300
    )
    return


@app.cell
def _(Wing, g, panel):

    wing = Wing("test_wing", g.P0(), [panel])

    loads, sloads = wing.run_avl([0, 0.2, 0.4])
    return


if __name__ == "__main__":
    app.run()
