
import freecad
from acdesign.aircraft import Plane
import freecad


def create_plane(plane, savepath):
    doc = App.newDocument()

    doc.addObject('PartDesign::Body','Body')

    doc.saveAs(u"/home/tom/projects/f3a_design/test2.FCStd")






