from app.ekf import PositionEkf


def test_filter_tracks_position_measurements() -> None:
    f = PositionEkf()
    for _ in range(20):
        f.predict(1.0, (0.0, 0.0, 0.0))
        f.update_position((10.0, -4.0, 2.0), 2.0)
    e, n, u = f.position
    assert abs(e - 10.0) < 0.5
    assert abs(n + 4.0) < 0.5
    assert abs(u - 2.0) < 0.5
    assert f.horizontal_sigma_m < 2.0
