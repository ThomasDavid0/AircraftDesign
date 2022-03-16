


class Propulsion:
    def __init__(self, capacity, v0, eta, n):
        self.capacity = capacity
        self.eta = eta
        self.v0 = v0
        self.n = n

    @staticmethod
    def lipo(cells, Ah):
        return Propulsion(Ah * 60 * 60, cells*4.0, 0.3, 1.3)

    def endurance(self, preq):
        return ((self.eta * self.v0 * self.capacity * 0.85 / preq ) ** self.n ) * 3600 ** (1 - self.n)

    @property
    def Ah(self):
        return self.capacity / (60*60*0.85)

    @property
    def lipo_cells(self):
        return self.v0 / 4.0