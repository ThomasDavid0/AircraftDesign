from .airfoil import Airfoil
from geometry import Transformation, Point, Quaternion, Euler, P0
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


    def __getattr__(self, name):
        if name in self.transform.cols:
            return getattr(self.transform, name)
        

    @staticmethod
    def create(airfoil, chord, panelpos: Point=P0(), te_thickness=0, incidence=0):
        return Rib(
            Transformation.build(
                panelpos,
                Euler(np.pi/2, 0, np.radians(incidence))
            ),
            airfoil,
            Airfoil.download(airfoil.split("_")[-1])
            .set_chord(chord)
            .set_te_thickness(te_thickness).points
        )

    def rename(self, name):
        return Rib(self.transform,name, self.points)

    def offset(self, pos):
        return Rib(
            Transformation.build(self.transform.translation + pos, self.transform.rotation),
            self.name, self.points
        )

    @property
    def incidence(self):
        cline = self.transform.rotate(Point(1,0,0))
        return np.arctan2(cline.y[0], cline.x[0])

    def scale(self, fac: float):
        return Rib(
            Transformation(self.transform.translation * fac, self.transform.rotation),
            self.name,
            self.points * fac
        )