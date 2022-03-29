from acdesign.aircraft.plane import ConventionalPlane
from acdesign.aircraft.wing import Wing



buddi = ConventionalPlane(
    "Buddi",
    Wing.double_taper(
        "wing",
        3200, 
        0.75*1e6, 
        0.6,  
        100, 
        ["fx63137-il","fx63137-il","mh32-il","mh32-il"]
    ),
    Wing.straight_taper(
        "tail",
        3200/4,
        0.75/3, 
        0.3,
        20
    ),
    Wing.straight_taper(
        "fin",
        3200/8,
        0.75/6,
        0.32,
        30,
        False
    )
)