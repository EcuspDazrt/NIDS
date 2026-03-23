import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from capture.capture import RunningStats
from features.extract_inference import extract_features_rf, extract_features_ae

def make_test_flow():
    fwd_byte_stats = RunningStats()
    bwd_byte_stats = RunningStats()
    fwd_byte_stats.update(100)
    fwd_byte_stats.update(200)
    bwd_byte_stats.update(150)

    return {
        'src_ip': b'\xc0\xa8\x00\x01',
        'dst_ip': b'\xc0\xa8\x00\x02',
        'src_port': 12345,
        'dst_port': 443,
        'protocol': 6,
        'fwd_packets': 2,
        'bwd_packets': 1,
        'fwd_bytes': 300,
        'bwd_bytes': 150,
        'fwd_iat_total': 0.5,
        'bwd_iat_total': 0.0,
        'start_time': 1000.0,
        'last_seen': 1002.0,
        'fwd_byte_stats': fwd_byte_stats,
        'bwd_byte_stats': bwd_byte_stats,
        'total_byte_stats': RunningStats(),
        'fwd_iat_stats': RunningStats(),
        'bwd_iat_stats': RunningStats(),
        'total_iat_stats': RunningStats(),
        'active_stats': RunningStats(),
        'idle_stats': RunningStats(),
        'syn_count': 1,
        'ack_count': 2,
        'fin_count': 1,
        'rst_count': 0,
        'ja3_hash': None,
    }

def test_rf_duration_in_seconds():
    flow = make_test_flow()
    features = extract_features_rf(flow)
    # duration should be 2.0 seconds, not 2,000,000 microseconds
    assert features['Duration'] == 2.0, f"Expected 2.0, got {features['Duration']}"

def test_rf_packet_rate_sensible():
    flow = make_test_flow()
    features = extract_features_rf(flow)
    # 3 total packets over 2 seconds = 1.5 packets/sec
    assert 1.0 < features['Total Packet Rate'] < 2.0, \
        f"Packet rate {features['Total Packet Rate']} out of expected range"

def test_ae_duration_log1p():
    flow = make_test_flow()
    features = extract_features_ae(flow)
    import numpy as np
    expected = np.log1p(2.0)
    assert abs(features['Duration'] - expected) < 1e-5, \
        f"Expected log1p(2.0)={expected:.4f}, got {features['Duration']:.4f}"

def test_iat_total_accumulator():
    flow = make_test_flow()
    features = extract_features_rf(flow)
    # forward IAT total should be 0.5 seconds
    assert features['Forward IAT'] == 0.5, \
        f"Expected 0.5, got {features['Forward IAT']}"

def test_in_out_ratio():
    flow = make_test_flow()
    features = extract_features_rf(flow)
    # 2 fwd / 1 bwd = 2.0
    assert abs(features['In/Out Ratio'] - 2.0) < 0.01

def test_no_nan_or_inf_rf():
    import numpy as np
    flow = make_test_flow()
    features = extract_features_rf(flow)
    for key, val in features.items():
        assert not (isinstance(val, float) and (np.isnan(val) or np.isinf(val))), \
            f"NaN or Inf in RF feature: {key}"

def test_no_nan_or_inf_ae():
    import numpy as np
    flow = make_test_flow()
    features = extract_features_ae(flow)
    for key, val in features.items():
        assert not (isinstance(val, float) and (np.isnan(val) or np.isinf(val))), \
            f"NaN or Inf in AE feature: {key}"