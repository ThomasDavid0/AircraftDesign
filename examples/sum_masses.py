from acdesign.aircraft.component_mass import ComponentMass
import numpy as np
import pandas as pd
from geometry import Point, Mass

df = pd.read_csv('examples/massprops.csv')

cmasses = []
for i, row in df.iterrows():
    cmasses.append(ComponentMass(row.component, Point(row.x, row.y, row.z), Mass.point(row.mass)))

total = ComponentMass.combine(cmasses)

pass



