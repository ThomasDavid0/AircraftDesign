from acdesign.aircraft import Panel, Rib
from typing import List
from geometry import Point, Transformation, Euler
import numpy as np



class WingProps:
    def __init__(self, w):
        self.S = sum([p.area for p in w.panels])
        self.b = (w.panels[-1].otbd.y + w.panels[-1].y)
        self.SMC = self.S / self.b

        self.MAC =  np.sum([p.MAC * p.area for p in w.panels]) / self.S
        yMAC = np.sum([(p.pMAC.y + p.y) * p.area for p in w.panels]) / self.S
        xMAC = np.sum([(p.pMAC.x + p.x) * p.area for p in w.panels]) / self.S
        self.pMAC = Point(xMAC, yMAC, 0)

class Wing:
    def __init__(self, panels: List[Panel]):
        self.panels = panels
        self.props = WingProps(self)

    def __getattr__(self, name):
        if name in self.props.__dict__:
            return getattr(self.props, name)
        raise AttributeError(f"Attribute {name} not found")

    @staticmethod
    def from_ribs(ribs: List[Rib]):
        panels = []
        for i, (r1, r2) in enumerate(zip(ribs[:-1], ribs[1:])):
            panels.append(Panel(
                f"wing_p{i}", 
                Transformation.build(
                    Point(-r1.x, r1.y, -r1.z), 
                    Euler(np.pi, 0, np.pi)
                ), 
                True, 
                r1.offset(-r1.transform.p),
                r2.offset(-r1.transform.p)
            ))
        return Wing(panels)

    def scale(self, fac: float):
        return Wing([p.scale(fac) for p in self.panels])


    # extend to centre

    # fill gaps

    #sort panels

