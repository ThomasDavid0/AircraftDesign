

import freecad
App= freecad.app
import Sketcher
import acdesign.cad.geom_to_freecad 
from acdesign.cad.create import create_rib
from acdesign.aircraft import Rib
import numpy as np
from geometry import Transformation, Point, Quaternion, Euler

rib = Rib.create("whitcomb-il", 100, Point(0, 200, 0), 5, np.radians(10))


doc = App.newDocument()

body = doc.addObject('PartDesign::Body','Body')
body.Placement = Transformation(
    Point(-200, 50, 0),
    Euler(0, np.pi, 0)
).to_placement()

sketch = create_rib(body, rib)
doc.recompute()
doc.saveAs("/home/tom/projects/f3a_design/test_airfoil.FCStd")
    
