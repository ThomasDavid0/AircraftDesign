
import numpy as np
from acdesign.avl.keywords import kwdict
from acdesign.avl.avl_runner import run_avl
from pathlib import Path
from itertools import chain

from acdesign.avl.parse_avl_output import parse_strip_forces
from acdesign.aircraft.wing import Wing
from acdesign.aircraft.wing_panel import WingPanel


wing = Wing(
    [
        WingPanel.trapezoidal(1.5, 1.5 * 0.4, 1, 0.25),
        WingPanel.elliptical_cr(3, 0.4, 0.25),
    ]
)

avlheader = kwdict["HEADER"](
    "MACE 1", 0, 1, 0, 0, wing.S, wing.smc, wing.b, -wing.smc / 4, 0, 0
)[1:]
avldata = wing.dump_avl(np.linspace(0, 1, 20), sections="flat")


Path("avl/geom.avl").write_text("\n".join(avlheader + avldata))

cls = np.linspace(0.1, 1.0, 5)

def run_cl(name: str, cl: float):
    return [
        f"a c {cl}",
        "x",
        f"ft total_forces_{name}.out",
        f"fs strip_forces_{name}.out",
    ]

run_avl(
    [
        "load geom.avl",
        "OPER",
        *chain(*[run_cl(i, cl)  for i, cl in enumerate(cls)]),
        "",
        "QUIT",
    ]
)

#sloads = [parse_strip_forces(Path(f"avl/strip_forces_{i}.out"), wing.b) for i in range(len(cls))]
