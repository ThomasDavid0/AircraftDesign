from pytest import fixture, approx
from acdesign.performance.performance import AeroModel, OperatingPoint, Propulsion, Performance
from acdesign.atmosphere import Atmosphere



def test_k():
    assert AeroModel(1.7, 1.7*0.2, 0.02, 1.5).k == approx(0.0452482219)

def test_performance():
    p = Performance(
        OperatingPoint(Atmosphere.alt(0), 26),
        AeroModel(1.7, 0.34, 0.02, 1.5),
        Propulsion.lipo(6, 12.75),
        5.0,
        0.0
    ) 

    assert p.CL ==  approx(0.348423393, 1e-4)
    assert p.CD ==  approx(0.026658, 0.1)
    assert p.D ==  approx(3.588839688, 0.1)


    assert p.preq == approx(93.30983189, 0.1)
    assert p.endurance == approx(2853.231176, 0.1)
    assert p.range == approx(74.18401057 * 1000, 0.1)



def test_optimize():
    pass