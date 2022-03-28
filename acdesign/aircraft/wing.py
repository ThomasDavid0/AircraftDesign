from acdesign.aircraft import Panel, Rib
from typing import List, Union
from geometry import Point, Transformation, Euler
import numpy as np



class WingProps:
    def __init__(self, w):
        self.S = sum([p.area for p in w.panels]) * 2 if w.symm else 1
        
        self.b = (w.panels[-1].otbd.y + w.panels[-1].y) * 2 if w.symm else 1

        self.AR = self.b**2 / self.S

        self.SMC = self.S / self.b
        self.tr = w.panels[-1].tip.chord / w.panels[0].root.chord
        
        self.MAC =  np.sum([p.MAC * p.area for p in w.panels]) / (self.S / 2)

        yMAC = np.sum([(p.pMAC.y + p.y) * p.area for p in w.panels]) / (self.S / 2)
        xMAC = np.sum([(p.pMAC.x + p.x) * p.area for p in w.panels]) / (self.S / 2)
        self.pMAC = Point(xMAC, yMAC, 0)


class Wing:
    def __init__(self, panels: List[Panel], symm=True):
        self.panels = panels
        self.symm=True
        self.props = WingProps(self)

    def __getattr__(self, name):
        if name in self.props.__dict__:
            return getattr(self.props, name)
        raise AttributeError(f"Attribute {name} not found")

    @staticmethod
    def from_ribs(ribs: List[Rib], symm=True):
        panels = []
        for i, (r1, r2) in enumerate(zip(ribs[:-1], ribs[1:])):
            panels.append(Panel(
                f"wing_p{i}", 
                Transformation.build(
                    Point(-r1.x, r1.y, -r1.z), 
                    Euler(np.pi, 0, np.pi)
                ), 
                [r1.offset(-r1.transform.p),
                r2.offset(-r1.transform.p)]
            ))
        return Wing(panels, symm)

    def scale(self, fac: float):
        return Wing([p.scale(fac) for p in self.panels])

    @staticmethod
    def buddi_uav(b, S, TR, le_sweep, section:Union[str, List[str]], kink_loc = 12*25.4+60):
        if isinstance(section, str):
            section = [section for _ in range(3)]
        
        a = kink_loc
        cr = 0.5*S / (a + (1 + TR) * (b/4 - a / 2))
        ct = TR * cr
        
        return Wing.from_ribs([
            Rib.create(section[0], cr, Point(0, 0, 0), 2),
            Rib.create(section[1], cr, Point(0, a, 0), 2),
            Rib.create(section[2], ct, Point(le_sweep, b/2, 0), 2),
        ], True)


    # extend to centre

    # fill gaps

    #sort panels

