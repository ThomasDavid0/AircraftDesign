
import numpy as np


class AeroModel:
    def __init__(self, b, S, CD0, CLmax):
        self.b = b
        self.S = S
        self.CD0 = CD0
        self.CLmax = CLmax

        self.AR = (self.b**2) / self.S
        self.k = 0.0078 + 1 / (np.pi * self.AR)

    

