# tests/test_alert_engine.py
from collections import deque
from multiprocessing import Queue, Event
from alerts.alert_engine import AlertEngine

def make_engine():
    q = Queue()
    e = Event()
    return AlertEngine(rf_threshold=2, ae_threshold=2,
                       results_queue=q, flash_event=e), q

def make_flow():
    return {
        'src_ip': b'\xc0\xa8\x00\x01',
        'dst_ip': b'\xc0\xa8\x00\x02',
        'src_port': 1234,
        'dst_port': 443,
        'protocol': 6,
    }

def test_rf_detection_fires():
    engine, q = make_engine()
    engine.evaluate(
        ae_category=0, rf_category=3,
        rf_score=0.95, ja3_hash=None,
        ja3_malicious=False, flow=make_flow()
    )
    assert not q.empty()
    alert = q.get()
    assert alert['payload']['type'] == 'EXPLICIT_ATTACK_DETECTION'

def test_rf_below_threshold_no_alert():
    engine, q = make_engine()
    engine.evaluate(
        ae_category=0, rf_category=1,
        rf_score=0.3, ja3_hash=None,
        ja3_malicious=False, flow=make_flow()
    )
    assert q.empty()

def test_ja3_match_fires():
    engine, q = make_engine()
    engine.evaluate(
        ae_category=0, rf_category=0,
        rf_score=0.1, ja3_hash='abc123',
        ja3_malicious=True, flow=make_flow()
    )
    assert not q.empty()
    alert = q.get()
    assert alert['payload']['type'] == 'JA3_MATCH'

def test_sustained_anomaly_fires_after_threshold():
    engine, q = make_engine()
    flow = make_flow()
    # push 10 flows with ae_category >= 2
    for _ in range(10):
        engine.evaluate(
            ae_category=3, rf_category=0,
            rf_score=0.1, ja3_hash=None,
            ja3_malicious=False, flow=flow
        )
    # should have fired sustained anomaly alert
    alerts = []
    while not q.empty():
        alerts.append(q.get())
    types = [a['payload']['type'] for a in alerts]
    assert 'SYSTEMIC_ANOMALY' in types

def test_sustained_anomaly_does_not_fire_below_threshold():
    engine, q = make_engine()
    flow = make_flow()
    # only 5 severe flows out of 10 — below the 6/10 threshold
    for i in range(10):
        engine.evaluate(
            ae_category=3 if i < 5 else 0,
            rf_category=0, rf_score=0.1,
            ja3_hash=None, ja3_malicious=False,
            flow=flow
        )
    alerts = []
    while not q.empty():
        a = q.get()
        if a['payload']['type'] == 'SYSTEMIC_ANOMALY':
            alerts.append(a)
    assert len(alerts) == 0