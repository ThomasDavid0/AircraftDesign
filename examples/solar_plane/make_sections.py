

from acdesign.airfoils.polar import UIUCPolar
from acdesign.solar_wing import SolarWing
from pathlib import Path


polar = UIUCPolar.local("SG6041")
airfoil = polar.airfoil()

wing = SolarWing.straight_to_elliptical(19, 18, 2, polar)

te_thick = 2

root_sec = airfoil.set_chord(wing.wing.panels[0].root_chord*1000).set_te_thickness(2).set_chord(1)
root_sec.dump_selig(Path("examples/solar_plane/SG6041_root.dat"))

tip_sec = airfoil.set_chord(120).set_te_thickness(2).set_chord(1)

tip_sec.dump_selig(Path("examples/solar_plane/SG6041_120mm.dat"))


pass