from pytest import fixture, approx
from acdesign.performance.performance import Performance
from acdesign.performance.propulsion import Motor, Battery, Propeller
from acdesign.atmosphere import Atmosphere
from .conftest import dmodel, wing, fd, op


@fixture
def bperf(dmodel):
    return Performance(
        op,
        dmodel,
        Propeller(),
        Motor(),
        Battery.lipo(6, 12.75),
    ) 


def test_performance(bperf):
    assert bperf.CL ==  approx(0.20637104707226153, 1e-4)
    assert bperf.CD ==  approx(0.0220547783291186, 0.1)
    assert bperf.D ==  approx(5.241950808460434, 0.1)

    assert bperf.preq == approx(120.56486859458998, 0.1)
    assert bperf.endurance == approx(2853.231176, 0.1)
    assert bperf.range == approx(74.18401057 * 1000, 0.1)



def test_optimize():
    pass