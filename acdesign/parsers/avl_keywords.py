from tkinter.messagebox import RETRY
from geometry import Point
from typing import List, Tuple, Union
from acdesign.aircraft import Panel, Rib, Plane
from collections import namedtuple
import itertools
from enum import Enum

kwfile = "acdesign/parsers/kwords.txt"


class AVLParam:
    def __init__(self, name, dtype, row, col, optional):
        self.name = name
        self.dtype = dtype
        self.row = row
        self.col = col
        self.optional = optional

    def collect(self, data: List[List[str]]) -> Union[str, float, int]:
        try:
            return self.dtype(data[self.row][self.col])
        except IndexError:
            assert self.optional, f"required parameter {self.name} missing"


def _read_kwordfile(file):
    #parse file and split on |
    with open(file, "r") as f:
        data = [l.strip().split("|") for l in f.readlines() if "|" in l]
    
    # break columns on spaces
    data = [[l.strip().split() for l in line] for line in data]

    #separate into keyword subsets
    _keydata = []
    for r in data:
        if "keyword" in r[1][0]:
            _keydata.append(([r[0]], [r[1]]))
        else:
            _keydata[-1][0].append(r[0])
            _keydata[-1][1].append(r[1])
    else:
        return _keydata


def get_dtype(example):
    if "." in example:
        return float
    else:
        try:
            int(example)
            return int
        except ValueError:
            return str


def _parse_kwfdata(kdata):
    parms = []
    
    for r, (rl, rr) in enumerate(zip(kdata[0], kdata[1])):
        for c, (cl, cr) in enumerate(zip(rl, rr)):
            
            if "keyword" in cr:
                keyword = cl
            else:
                opt = cr[0]=="!"

                parms.append(AVLParam(
                    cr[1:] if opt else cr, 
                    get_dtype(cl), 
                    r, c, opt
                ))
            
    return keyword,parms
    
        
class KeyWord:
    def __init__(self, word: str, parms: List[AVLParam]):
        self.word = word
        self.parms= parms
        self.NTuple = namedtuple(word.title(), [parm.name for parm in self.parms])
    
    def parse(self, data:str) -> namedtuple:
        data = [line.split() for line in data]
        return self.NTuple(**{p.name: p.collect(data) for p in self.parms})




kwlist = [KeyWord(*_parse_kwfdata(kwfd)) for kwfd in _read_kwordfile(kwfile)]
kwdict = {kw.word: kw for kw in kwlist}
kw4dict = {kw.word[:4]: kw for kw in kwlist}
