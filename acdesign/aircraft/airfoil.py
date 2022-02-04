import urllib.request
from urllib.error import HTTPError
from geometry import Points, Point
import numpy as np


class Airfoil:
    def __init__(self, name, points: Points):
        self.name = name
        self.points = points

    @staticmethod
    def parse_selig(file):      
                
        with open(file) as f:
            lines = f.readlines()
        
        data = np.array([l.strip().split()  for l in lines[1:]]).astype(float)

        return Airfoil(
            lines[0].strip(), 
            Points(
                np.append(data, np.zeros((len(data), 1)), axis=1) 
            )
        )

    @staticmethod
    def download(airfoiltoolsname):
        _file = urllib.request.urlretrieve("http://airfoiltools.com/airfoil/seligdatfile?airfoil=" + airfoiltoolsname)            
        return Airfoil.parse_selig(_file[0])

    @property
    def te_thickness(self):
        return self.points[0].y - self.points[-1].y

    @property
    def chord(self):
        return self.points[0].x

    @property
    def thickness(self):
        return max(self.points.y) - min(self.points.y)

    def set_te_thickness(self, thick:float):        
        surfaces = -np.sign(np.gradient(self.points.x))

        xunit = self.points.x / self.chord

        te_diff = Points.Y(0.5 * (thick - self.te_thickness) * xunit * surfaces)
        return Airfoil(self.name, self.points + te_diff)

    def set_chord(self, chord):
        return Airfoil(self.name, self.points * chord / self.chord)

    