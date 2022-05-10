from geometry import Point, Transformation, Q0



class Body:
    def __init__(self, name:str, transform: Transformation):
        self.name = name
        self.transform = transform

    @staticmethod
    def create(name, acpos):
        return Body(name, Transformation(Point(**acpos), Q0()))

    @staticmethod
    def simple(name):
        return Body(name, Transformation())

    def dumpd(self):
        return dict(
            name=self.name,
            acpos=self.transform.translation.to_dict()
        )