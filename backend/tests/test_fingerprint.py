from pathlib import Path

from app.fingerprint import FingerprintEngine
from app.schemas import CellObservation, WifiObservation
from app.storage import Storage


def test_wifi_and_cell_anchor_estimation(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    engine = FingerprintEngine(storage)
    wifi = [WifiObservation(bssid="aa:bb:cc:dd:ee:ff", rssi_dbm=-50)]
    cells = [CellObservation(key="lte:510:10:123:456", technology="LTE", signal_dbm=-90, registered=True)]
    engine.learn(-7.2, 112.7, 10.0, wifi, cells)
    w = engine.estimate_wifi(wifi)
    c = engine.estimate_cell(cells)
    assert w is not None and w[2] == 1
    assert c is not None and c[2] == 1
    assert abs(w[0][0] + 7.2) < 1e-9
    assert abs(c[0][1] - 112.7) < 1e-9
