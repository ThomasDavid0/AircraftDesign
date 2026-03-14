from dataclasses import dataclass
from itertools import chain
import geometry as g

from acdesign.aircraft.wings import Wings

from acdesign.avl.keywords import kwdict

@dataclass
class Aircraft:
    """An aircraft in AVL sign convention x aft, y right, z up. """
    name: str
    components: list[Wings]
    ref_wing: int # index of component to use for reference area, span, and chord
    reference_point: g.Point
    mass: g.Mass

    def __post_init__(self):
        self.S = self.components[self.ref_wing].S
        self.b = self.components[self.ref_wing].b
        self.C = self.components[self.ref_wing].C

    def plot(self, npoints: int = 100, shift: g.Point = None, fig = None, mode="lines"):
        import plotly.graph_objects as go
        fig = fig or go.Figure()
        fig = g.Coord.zero().plot(fig=fig, scale=0.2)

        shift = shift or g.P0()
        for component in self.components:
            fig = component.plot(npoints, shift, fig, mode)
        return fig
    
    def dump_avl(self):
        avl_header = kwdict["HEADER"](
            self.name, 0, 0, 0, 0, self.S, self.C, self.b, self.reference_point.x[0], self.reference_point.y[0], self.reference_point.z[0]
        )[1:]
        avl_components = list(chain(*[c.avl_component(i+1) for i, c in enumerate(self.components)]))
        return avl_header + avl_components