
import freecad
App=freecad.app
import Part
import Surface
import Sketcher
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

    loft = body.newObject('PartDesign::AdditiveLoft','AdditiveLoft')
    loft.Profile = skt1
    loft.Sections = [skt2]
    #    surf = doc.addObject("Surface::Sections","Surface")
 #   surf.NSections = [(skt1, "Edge1"),(skt1, "Edge1")]

    body.Placement = panel.transform.to_placement()
    return body
    

def create_rib(body, rib: Rib):
    sketch = body.newObject('Sketcher::SketchObject',rib.name)
    #sketch.Label = rib.name
    spline = Part.BSplineCurve(
            rib.points.to_vectors(),
            None,None,False,3,None,False
        )
    splineid = sketch.addGeometry(spline,False)
    line = Part.LineSegment(spline.StartPoint,spline.EndPoint)
    lineid = sketch.addGeometry(line)

    sketch.addConstraint(Sketcher.Constraint('Coincident',splineid,1,lineid,1))
    sketch.addConstraint(Sketcher.Constraint('Coincident',splineid,2,lineid,2))

    sketch.Placement = rib.transform.to_placement()
    return sketch

