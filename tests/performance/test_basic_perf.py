from pytest import fixture, approx
from acdesign.performance.performance import AeroModel, OperatingPoint, Propulsion, Performance
from acdesign.atmosphere import Atmosphere



def test_k():
    assert AeroModel(1.7, 1.7*0.2, 0.2, 0.02, 1.5).k == approx(0.0452482219)

def test_performance():
    p = Performance(
        OperatingPoint(Atmosphere.alt(0), 26),
        AeroModel(1.7, 0.525, 0.2, 0.02, 1.5),
        Propulsion.lipo(6, 12.75),
        5.0,
        0.0
    )
    
    assert p.CL ==  approx(0.383598, 1e-4)
    assert p.CD ==  approx(0.026658, 0.1)
    assert p.D ==  approx(5.794847, 0.1)


    assert p.preq == approx(144.1777, 0.1)
    assert p.endurance == approx(1726.716, 0.1)
    assert p.range == approx(44894.6, 0.1)



def test_optimize():
    pass