from geometry import Point, Transformation



class Body:
    def __init__(self, name:str, transform: Transformation):
        self.name = name
        self.transform = transform

    @staticmethod
    def create(name):
        return Body(name, Transformation())