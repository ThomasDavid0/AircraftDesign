

import pytest
import freecad
App= freecad.app
import Sketcher

from acdesign.cad.create import create_rib
from acdesign.aircraft import Rib
from geometry import Point
import numpy as np

@pytest.fixture
def rib():
    return Rib.create("n63412-il", Point(0, 200, 0), 200, np.radians(5), 5)


@pytest.fixture
def doc():
    return App.newDocument()

@pytest.fixture
def body(doc):
    return doc.addObject('PartDesign::Body','Body')
    

def test_create_rib(body, rib):
    sketch = create_rib(body, rib)
    
