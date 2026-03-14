from acdesign.aircraft.wing import Wing
from dataclasses import dataclass
import geometry as g
from itertools import chain


@dataclass
class Wings:
    """One component in AVL, so this could be a T tail, or something like that. 
    It is not necessarily the entire set of wings on the aircraft."""
    offset: g.Point
    wings: list[Wing]

    def __post_init__(self):
        self.S = sum(w.S for w in self.wings)
        self.b = max(w.b for w in self.wings)
        self.C = max(w.smc for w in self.wings)

    def avl_component(self, component_id: int):
        return list(chain(*[w.dump_avl(component_id, self.offset) for w in self.wings]))

    def dump_avl(self, component_id: int, translate: g.Point = None):
        translate = translate or g.Point(0, 0, 0)
        odata = [""]
        for wing in self.wings:
            odata += wing.dump_avl(self.offset + translate, component_id)
        return odata
    
    def plot(self, npoints: int = 100, shift: g.Point = None, fig = None, mode="lines"):        
        for wing in self.wings:
            fig = wing.plot(npoints, self.offset + (shift or g.P0()), fig, mode)
        return fig