from .airfoil import Airfoil
from geometry import Transformation, Point, Quaternion


class Rib:
    def __init__(self, transform: Transformation, airfoil: Airfoil):
        """A rib represents a positioned airfoil

        Args:
            transform (Transformation): from wing frame to x axis length of section, y axis thick direction, z outboard
            airfoil (Airfoil): represents the section points
        """
        self.transform = transform
        self.airfoil = airfoil

    @staticmethod
    def create(airfoil: Airfoil, x: float, y: float, incidence: float):
        return Rib(
            Transformation(
                Point(x,y,0), 
                Quaternion.zero().rotate(Point(0, -incidence, 0))
            ),
            airfoil
        )

    