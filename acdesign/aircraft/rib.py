from .airfoil import Airfoil
from geometry import Transformation, Point, Quaternion, Euler


class Rib(Airfoil):
    def __init__(self, transform: Transformation, *args, **kwargs):
        """A rib represents a positioned airfoil

        Args:
            transform (Transformation): from wing frame to x axis length of section, y axis thick direction, z outboard
            airfoil (Airfoil): represents the section points
        """
        self.transform = transform
        super().__init__(*args, **kwargs)

    @staticmethod
    def create(airfoil_name, panelpos: Point, chord, incidence, te_thickness):
        return Rib(
            Transformation(
                Point(panelpos.y,0,panelpos.z),
                Euler(0, incidence, 0)
            ),
            airfoil_name,
            Airfoil.download(airfoil_name).set_chord(chord).set_te_thickness(te_thickness).points
        )
