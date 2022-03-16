
import numpy as np


class AeroModel:
    def __init__(self, b, S, MAC, CD0, CLmax):
        self.b = b
        self.S = S
        self.MAC = MAC
        self.CD0 = CD0
        self.CLmax = CLmax

    @property
    def AR(self):
        return self.b / self.MAC

    @property
    def k(self):
        return 0.0078 + 1 / (np.pi * self.AR)
    

