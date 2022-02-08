
import freecad
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
            [
                App.Vector(75.1154,-18.9585),
            ],
            None,
            None,
            False,
            3,
            None,
            False
        ),
        False
    )


    sketch.AttachmentOffset.Base=App.Vector(rib.transform.to_list())




if __name__ == '__main__':
    plane = parse_plane("tests/aircraft.json")
    create_plane(plane,"/home/tom/projects/f3a_design/test2.FCStd")