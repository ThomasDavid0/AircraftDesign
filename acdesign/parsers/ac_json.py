from acdesign.aircraft import Plane, Airfoil, Rib, Panel
from geometry import Transformation, Point, Quaternion


def parse_rib(data: dict):
    return Rib.create(
        data["airfoil"],
        Point(data["sweep"], 0, data["span"]),
        data["chord"],
        data["incidence"],
        data["te_thickness"]
    )


def parse_panel(data: dict):
    return Panel(
        Transformation(
            Point(data["x"], 0.0, data["z"]),
            Quaternion.from_euler((data["dihedral"], data["incidence"], 0.0))
        ),
        data["symm"],
        parse_rib(data["inbd"]),
        parse_rib(data["otbd"]),
    )

    
def parse_plane(data: dict):
    pass