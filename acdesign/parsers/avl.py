from tkinter.messagebox import RETRY
from geometry import Point




def get_avl_data(file: str):
    with open(file, 'r') as f:
        avldata = [l.strip().replace("#", "!").split("!")[0] for l in f.readlines()]
    avldata = [l for l in avldata if not len(l) == 0]
    return avldata


def parse_avl_line(line:str):
    return [float(v) for v in line.split()]



def break_file(avldata):
    startsurf = [i for i, line in enumerate(avldata) if line in ["SURFACE", "BODY"]] + [len(avldata)]
    case_name = avldata[0]
    header = avldata[1:startsurf[0]]
    surfaces = [avldata[start:stop] for start, stop in zip(startsurf[:-1], startsurf[1:])]
    return case_name, header, surfaces


def parse_header(header):
    inertia = parse_avl_line(header[1])
    scb = parse_avl_line(header[2])
    headerdata =  dict(
        Mach = float(header[0]),
        iysym=inertia[0],
        izsym=inertia[1],
        zsym=inertia[2],
        sref=scb[0],
        cref=scb[1],
        bref=scb[2],
        momref = Point(*parse_avl_line(header[3]))
    )
    if len(header) == 5:
        headerdata["cdp"] = float(header[4])

    return headerdata