from tkinter.messagebox import RETRY
from geometry import Point
from typing import List, Tuple, Union, Dict, NamedTuple
from acdesign.aircraft import Panel, Rib, Plane, Body
from collections import namedtuple
import itertools
from enum import Enum
from .avl_keywords import kwdict, kw4dict, KeyWord, AVLParam
import numpy as np

def get_avl_data(file: str):
    with open(file, 'r') as f:
        avldata = [l.strip().replace("#", "!").split("!")[0] for l in f.readlines()]
    return ["HEADER"] + [l for l in avldata if not len(l) == 0]
    


def getkw(line: str, err: str=None) -> Union[None, KeyWord]:
    if len(line) > 4:
        if line[:4] in kw4dict.keys():
            return kw4dict[line[:4]]
    if err:
        raise KeyError(err)
    

def break_file(avldata: List[str]) -> List[List[str]]:
    brkids = [i for i, line in enumerate(avldata) if getkw(line)] + [len(avldata)]
    return [avldata[start:stop] for start, stop in zip(brkids[:-1], brkids[1:])]


def read_avl(avlsecs: List[List[str]]) -> List[NamedTuple]:   
    return [getkw(sec[0], f"Keyword {sec[0]} not found").parse(sec) for sec in avlsecs]



def break_tuples(avltups: List[NamedTuple], keywords) -> Dict[str, List[List[NamedTuple]]]:
    odict = {key: [] for key in keywords}
    active = None
    for tup in avltups:
        for kw in keywords:
            if tup.__class__.__name__ == kw:
                odict[kw].append([])
                active = kw
        
        if active:
            odict[active][-1].append(tup)
    return odict



def parse_avl_section(avltups: List[namedtuple]) -> dict:
    tups = break_tuples(avltups, ["Section", "Control", "Naca", "Claf", "Cdcl", "Afile"])
    refdat = tups["Section"][0][0]
    return dict(
        airfoil = f"n{tups['Naca'][0].section}-il" if len(tups["Naca"]) > 0 else "naca0010-il",
        chord = refdat.Chord,
        te_thickness = refdat.Chord / 50,
        incidence = refdat.Ainc
    )


def parse_avl_surface(avltups: List[namedtuple]) -> List[dict]:
    tups = break_tuples(avltups, [
        "Surface", 
        "Section", 
        "Yduplicate", 
        "Angle",
        "Scale",
        "Translate",
        "Nowake",
        "Noable",
    ])

    refdat=tups["Surface"][0][0]
    panels = []

    #our panels can only have two ribs so may need to create more than one per Surface
    for rl, tl in zip(tups["Section"][:-1], tups["Section"][1:]):
        rt=rl[0]
        tt=tl[0]
        rp = Point(rt.Xle, rt.Yle, rt.Zle)
        tp = Point(tt.Xle, tt.Yle, tt.Zle)
        dp = tp - rp

        panels.append(dict(
            name=refdat.name,
            acpos=rp.to_dict(),
            dihedral=np.arctan2(dp.z, dp.y),
            incidence=0,
            symm=len(tups["Yduplicate"]) > 0,
            length=dp.y,
            sweep=dp.x,
            inbd = parse_avl_section(rl),
            otbd = parse_avl_section(tl)
        ))
    
        #panels[-1]["refdata"] = tups["Surface"][0]
    return panels 


def parse_avl_body(avltups: List[namedtuple]) -> List[dict]:
    tups = break_tuples(avltups, ["Body"])
    return [[]]


def parse_avl_ac(avltups: List[namedtuple]) -> Plane:
    tups = break_tuples(avltups, ["Header", "Surface", "Body"])

    plane = Plane.create(
        tups["Header"][0][0].name,
        [p for p in itertools.chain(*[parse_avl_surface(s) for s in tups["Surface"]])],
        [b for b in itertools.chain(*[parse_avl_body(b) for b in tups["Body"]])],
        0.01
    )
    plane.refdata = tups["Header"][0][0]
    return plane


def parse_avl(file) -> Plane:
    return parse_avl_ac(read_avl(break_file(get_avl_data(file))))
    