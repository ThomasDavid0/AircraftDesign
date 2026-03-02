from acdesign.aircraft.wing import Wing
from flightdata.base import Collection
from dataclasses import dataclass
import geometry as g
import numpy as np
import numpy.typing as npt
from acdesign.avl.keywords import kwdict
from acdesign.airfoils.airfoil import Airfoil
from itertools import chain

@dataclass
class PlacedWing(Wing):
    name: str
    translate: g.Point  # position of
    dihedral: float  # radians
    symm: bool = True
    ydupl: bool = True
    

    @property
    def dihedral_rotation(self) -> g.Quaternion:
        return g.Euler(self.dihedral, 0, 0)

    def world_le(self, y: npt.NDArray[np.float64], place: bool = False) -> g.Point:
        return (self.translate if place else g.P0()) + self.dihedral_rotation.transform_point(
            g.PX(self.le(y)) + g.PY(y) * self.b
        )

    def world_te(self, y: npt.NDArray[np.float64], place: bool = False) -> g.Point:
        return (self.translate if place else g.P0()) + self.dihedral_rotation.transform_point(
            g.PX(self.le(y) + self.C(y)) + g.PY(y) * self.b
        )


    def dump_avl(
        self,
        ylocs: npt.NDArray[np.float64] | None,
        sections: list[str] | str = "flat",
        component: int = None,
    ):

        if ylocs is None:
            if self.symm:
                ylocs = 0.5 * np.cumsum([0.0] + [p.b for p in self.panels]) / self.b
            else:
                ylocs = np.cumsum([0.0] + [p.b for p in self.panels]) / self.b

        ylocs = np.atleast_1d(ylocs)
        odata = [""]
        odata += kwdict["SURFACE"](self.name, 12, 0.0, 20, 0.0)

        le = self.world_le(ylocs, place=False)
        C = self.C(ylocs)

        if component is not None:
            odata += kwdict["COMPONENT"](component)

        if self.ydupl:
            odata += kwdict["YDUPLICATE"](0.0)

        if not self.translate == 0:
            odata += kwdict["TRANSLATE"](self.translate.x[0], self.translate.y[0], self.translate.z[0])


        for i in range(len(ylocs)):

            _p, _y = self.get_panel(ylocs[i])

            odata += kwdict["SECTION"](le.x[i], le.y[i], le.z[i], C[i], 0)

            if not sections == "flat":
                Airfoil.parse_selig(
                    "src/data/uiuc/" + sections[i].name + ".dat"
                ).dump_selig(f"avl/{sections[i].name}.dat")

                if sections != "flat":
                    odata += kwdict["AFILE"](None, None, sections[i].name + ".dat")
            
            if len(_p.controls) > 0:
                for control in _p.controls:
                    odata += kwdict["CONTROL"](
                        control.name,
                        1.0,
                        control.root_prop,
                        0, 0, 0, control.sdup
                    )

        return odata


class Wings(Collection):
    VType = PlacedWing
    uid = "name"


    def avl_component(self, component: int):
        
        return list(chain(*[w.dump_avl(None, "flat", component) for w in self]))



