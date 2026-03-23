import json
from pathlib import Path

def test_thresholds_file_exists():
    path = Path('models/artifacts/thresholds.json')
    assert path.exists()

def test_thresholds_structure():
    with open('models/artifacts/thresholds.json') as f:
        t = json.load(f)
    assert 'rf' in t and 'rf_binary' in t
    assert 'ae' in t and 'ae_binary' in t and 'ae_max' in t
    assert len(t['rf']) == 3
    assert len(t['ae']) == 3

def test_thresholds_ordered():
    with open('models/artifacts/thresholds.json') as f:
        t = json.load(f)
    ae = t['ae']
    assert ae[0] < ae[1] < ae[2] < t['ae_max'], \
        "AE thresholds should be strictly increasing"
    rf = t['rf']
    assert rf[0] < rf[1] < rf[2], \
        "RF thresholds should be strictly increasing"

def test_thresholds_in_valid_range():
    with open('models/artifacts/thresholds.json') as f:
        t = json.load(f)
    assert 0.0 < t['rf_binary'] < 1.0
    assert 0.0 < t['ae_binary']
    assert all(0.0 < v for v in t['ae'])