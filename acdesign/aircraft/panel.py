from geometry import Point, Transformation

from .rib import Rib


class Panel:
    def __init__(
        self, 
        transform: Transformation, 
        symm: bool,
        inbd: Rib, 
        otbd: Rib
    ):
        """A panel represents a constant taper section of wing, tail, fin etc.  
        left wing is modelled, sym reflects to right wing.

        Args:
            transform (Transformation): from body frame to y axis along length of panel, x axis aft, z down
            symm (bool): [description]
            length (float): [description]
            le_sweep (float): [description]
            twist (float): [description]
            inbd (Airfoil): [description]
            otbd (Airfoil): [description]
        """
        self.transform = transform
        self.symm = symm
        self.inbd = inbd
        self.otbd = otbd