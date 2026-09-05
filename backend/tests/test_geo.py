from app.geo import enu_to_lla, lla_to_enu


def test_local_roundtrip() -> None:
    origin = (-7.2756, 112.7932, 12.0)
    target = (-7.2749, 112.7941, 18.0)
    enu = lla_to_enu(*target, origin)
    back = enu_to_lla(*enu, origin)
    assert abs(back[0] - target[0]) < 1e-10
    assert abs(back[1] - target[1]) < 1e-10
    assert abs(back[2] - target[2]) < 1e-10
