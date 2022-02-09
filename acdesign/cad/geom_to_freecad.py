from geometry import Point, Points, Quaternion, Quaternions, Transformation
import freecad
App = freecad.app


setattr(Point, "to_vector", lambda self: App.Vector(*self.to_list()))
setattr(Points, "to_vectors", lambda self: [p.to_vector() for p in self])
setattr(Quaternion, "to_rotation", lambda self: App.Rotation(self.x, self.y, self.z, self.w))
setattr(Quaternions, "to_rotations", lambda self: [q.to_rotation() for q in self])


def t_to_placement(self: Transformation):
    return App.Placement(
        self.translation.to_vector(), 
        self.rotation.to_rotation()
    )

setattr(Transformation, "to_placement", t_to_placement)

