import xml.etree.ElementTree as ET

from geometry import Point
from acdesign.old_aircraft.plane import Plane
from acdesign.old_aircraft.panel import Panel

from acdesign.airfoils.airfoil import Airfoil


def parse_xflr_plane(file: str) -> Plane:
    rt = ET.parse(file).getroot()

    assert rt.attrib["version"] == "1.0"

    plane = rt.find("Plane")
    
    return Plane(
        plane.find("Name").text,
        plane.findall("wing"),
        None
    )


def parse_xflr_wing(wing) -> Panel: 
    return Panel(
        wing.find("Name").text,
        Point(*[float(i) for i in wing.find("Position").text.split(",")]),
        bool(wing.find("Symetric").text),
        wing.find("Sections").findall("Section")
    )

