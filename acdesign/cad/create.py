
import freecad
App=freecad.app
import Part
import acdesign.cad.geom_to_freecad
from acdesign.aircraft import Plane
import freecad


def create_plane(plane, savepath):
    doc = App.newDocument()

    doc.addObject('PartDesign::Body','Body')

    doc.saveAs(savepath)

    return doc


def create_panel(doc, panel):
    body = doc.addObject('PartDesign::Body','Body')


def create_rib(body, rib):
    
    #create sketch 
    sketch = body.newObject('Sketcher::SketchObject','Sketch')
    
    #create spline
    sketch.addGeometry(
        Part.BSplineCurve(
            rib.points.to_vectors(),
            None,None,False,3,None,False
        ),
        False
    )
    sketch.Placement = rib.transform.to_placement()
    return sketch


if __name__ == '__main__':
    from acdesign.parsers.ac_json import parse_plane
    plane = parse_plane("tests/aircraft.json")
    create_plane(plane,"/home/tom/projects/f3a_design/test2.FCStd")