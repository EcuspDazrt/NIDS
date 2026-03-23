import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_log_flow_writes_to_db():
    import gc
    from alerts.logger import init_db, log_flow

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = Path(f.name)

    with patch('alerts.logger.FLOW_DB_PATH', temp_db):
        init_db()

        flow = {
            'src_ip': b'\xc0\xa8\x00\x01',
            'dst_ip': b'\xc0\xa8\x00\x02',
            'src_port': 1234,
            'dst_port': 443,
            'protocol': 6,
        }
        ae_features = {'Duration': 1.0, 'In/Out Ratio': 0.5}

        log_flow(flow, 50, 2, 1, 0.3, 0.8,
                 ae_features_dict=ae_features,
                 rf_features_dict=None,
                 ja3_hash=None,
                 ja3_malicious=0)

        with sqlite3.connect(temp_db) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM flow_logs").fetchone()
            assert row is not None
            assert row['src_ip'] == '192.168.0.1'
            assert row['dst_ip'] == '192.168.0.2'
            assert row['ae_percent'] == 50
            assert row['ae_category'] == 2
            assert row['rf_category'] == 1
        # conn closes here via context manager

    # force garbage collection to release any lingering sqlite handles
    gc.collect()

    # retry unlink with small delay for Windows file lock release
    import time
    for _ in range(5):
        try:
            temp_db.unlink()
            break
        except PermissionError:
            time.sleep(0.1)


def test_ip_to_str_ipv4():
    from alerts.logger import ip_to_str
    result = ip_to_str(b'\xc0\xa8\x00\x01')
    assert result == '192.168.0.1'


def test_ip_to_str_ipv6():
    from alerts.logger import ip_to_str
    result = ip_to_str(b'\x00' * 15 + b'\x01')
    assert result == '::1'


def test_ip_to_str_none():
    from alerts.logger import ip_to_str
    assert ip_to_str(None) is None