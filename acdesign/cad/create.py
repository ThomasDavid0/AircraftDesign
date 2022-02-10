
import freecad
App=freecad.app
import Part
import Surface
import acdesign.cad.geom_to_freecad
from acdesign.aircraft import Plane, Panel, Rib
import freecad


def create_plane(plane, savepath):
    doc = App.newDocument()
    bodies = [create_panel(doc, panel) for panel in plane.panels]
    doc.recompute()
    doc.saveAs(savepath)
    return doc


def create_panel(doc, panel: Panel):
    body = doc.addObject('PartDesign::Body', panel.name)
    body.Label = panel.name
    skt1 = create_rib(body, panel.inbd.rename(f"{panel.name}_inbd_{panel.inbd.name}"))
    skt2 = create_rib(body, panel.otbd.rename(f"{panel.name}_otbd_{panel.otbd.name}"))

#    surf = doc.addObject("Surface::Sections","Surface")
 #   surf.NSections = [(skt1, "Edge1"),(skt1, "Edge1")]

  #  surf.Placement = panel.transform.to_placement()
    return body
    

def create_rib(body, rib: Rib):
    sketch = body.newObject('Sketcher::SketchObject',rib.name)
    #sketch.Label = rib.name
    edge = sketch.addGeometry(
        Part.BSplineCurve(
            rib.points.to_vectors(),
            None,None,False,3,None,False
        ),
        False
    )

    sketch.Placement = rib.transform.to_placement()
    return sketch

