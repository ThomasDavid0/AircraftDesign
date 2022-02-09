from .airfoil import Airfoil
from geometry import Transformation, Point, Quaternion, Euler
import numpy as np

class Rib(Airfoil):
    def __init__(self, transform: Transformation, *args, **kwargs):
        """A rib represents a positioned airfoil

        Args:
            transform (Transformation): position of airfoil relative to panel
            airfoil (Airfoil): represents the section points
        """
        self.transform = transform
        super().__init__(*args, **kwargs)

    @staticmethod
    def create(airfoil_name, chord, panelpos: Point=Point.zeros(), te_thickness=0, incidence=0):
        return Rib(
            Transformation(
                Point(0, panelpos.y, panelpos.z),
                Euler(np.pi/2, incidence, 0)
            ),
            airfoil_name,
            Airfoil.download(airfoil_name).set_chord(chord).set_te_thickness(te_thickness).points
        )

    def offset(self, pos):
        return Rib(
            self, 
            Transformation(self.transfrom.point + pos, self.transfrom.Quaternion),
            self.name, self.points
        )
    