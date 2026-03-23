from capture.capture import get_flow, make_canonical, RunningStats

def test_get_flow_creates_new():
    state = {}
    flow_id = (0, b'\xc0\xa8\x00\x01', b'\xc0\xa8\x00\x02', 1234, 443, 6)
    flow = get_flow(flow_id, state)
    assert flow_id in state
    assert flow['fwd_packets'] == 0
    assert flow['fwd_iat_total'] == 0.0
    assert flow['bwd_iat_total'] == 0.0

def test_get_flow_returns_existing():
    state = {}
    flow_id = (0, b'\xc0\xa8\x00\x01', b'\xc0\xa8\x00\x02', 1234, 443, 6)
    flow1 = get_flow(flow_id, state)
    flow1['fwd_packets'] = 5
    flow2 = get_flow(flow_id, state)
    assert flow2['fwd_packets'] == 5  # same object

def test_make_canonical_consistent():
    # same connection from either direction should produce same canonical form
    forward  = (b'\xc0\xa8\x00\x01', b'\xc0\xa8\x00\x02', 1234, 443, 6)
    backward = (b'\xc0\xa8\x00\x02', b'\xc0\xa8\x00\x01', 443, 1234, 6)
    assert make_canonical(forward) == make_canonical(backward)

def test_running_stats():
    stats = RunningStats()
    stats.update(10.0)
    stats.update(20.0)
    stats.update(30.0)
    assert stats.mean == 20.0
    assert stats.min == 10.0
    assert stats.max == 30.0
    assert stats.n == 3