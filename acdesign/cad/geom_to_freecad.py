from geometry import Point, Points, Quaternion, Quaternions, Transformation
import freecad



setattr(Point, "fc_vector", lambda self: App.Vector(*self.to_list()))
setattr(Points, "fc_vectors", lambda self: [p.fc_vector() for p in self])
setattr(Quaternion, "fc_rotation", lambda self: App.Rotation(*self.to_list()))
setattr(Quaternions, "fc_rotations", lambda self: [App.Rotation(*q.to_list()) for q in self])


def t_to_placement(self: Transformation):
    return App.Placement(
        self.translation.fc_vector(), 
        self.rotation.fc_vector()
    )

setattr(Transformation, "fc_placement", t_to_placement)

