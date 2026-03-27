import sys
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('NIDS.NetworkIntrusionDetection')
    from windows_toasts import WindowsToaster, Toast, ToastDisplayImage, ToastDuration
    APP_ID = 'NIDS.NetworkIntrusionDetection'
    toaster = WindowsToaster(APP_ID)

import sqlite3
import logging
import json
import socket
from datetime import datetime, timezone

from pathlib import Path
BASE_DIR = Path(__file__).parent
FLOW_DB_PATH = BASE_DIR.parent / 'data' / 'nids_flows.db'
ALERT_DB_PATH = BASE_DIR.parent / 'data' / 'nids_alerts.db'
LOG_PATH = BASE_DIR.parent / 'data' / 'nids_alerts.log'

ICON_PATH = BASE_DIR.parent / 'gui' / 'resources' / 'nids_logo.png'

logger = logging.getLogger('nids_alerts')
logger.setLevel(logging.INFO)

LOG_PATH.parent.mkdir(exist_ok=True)
handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def ip_to_str(ip_bytes):
    if ip_bytes is None:
        return None
    try:
        if len(ip_bytes) == 4:
            return socket.inet_ntop(socket.AF_INET, ip_bytes)
        elif len(ip_bytes) == 16:
            return socket.inet_ntop(socket.AF_INET6, ip_bytes)
    except Exception:
        return str(ip_bytes)

def init_db():
    FLOW_DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(FLOW_DB_PATH) as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS flow_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT NOT NULL,
            src_ip        TEXT,
            dst_ip        TEXT,
            src_port      INTEGER,
            dst_port      INTEGER,
            protocol      INTEGER,
            ae_score      REAL,
            ae_category   INTEGER,
            rf_score      REAL,
            rf_category   INTEGER,
            ae_percent    INTEGER,
            ae_features   TEXT,
            rf_features   TEXT,
            ja3_hash      TEXT,
            ja3_malicious BOOLEAN
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON flow_logs(timestamp)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_rf_category ON flow_logs(rf_category)
        ''')

    with sqlite3.connect(ALERT_DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS alert_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            type      TEXT,
            severity  INTEGER,
            message   TEXT,
            timestamp TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON alert_logs(timestamp)
        ''')

def log_flow(flow, ae_percent, ae_category, rf_category, ae_score, rf_score, ae_features_dict, rf_features_dict, ja3_hash, ja3_malicious):
    conn = sqlite3.connect(FLOW_DB_PATH)
    try:
        conn.execute(
            "INSERT INTO flow_logs "
            "(timestamp, src_ip, dst_ip, src_port, dst_port, protocol, "
            "ae_score, ae_category, rf_score, rf_category, ae_percent, ae_features, rf_features, ja3_hash, ja3_malicious) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                ip_to_str(flow.get('src_ip')),
                ip_to_str(flow.get('dst_ip')),
                int(flow.get('src_port', 0)),
                int(flow.get('dst_port', 0)),
                int(flow.get('protocol', 0)),
                float(ae_score),
                int(ae_category),
                float(rf_score),
                int(rf_category),
                int(ae_percent),
                json.dumps(ae_features_dict) if ae_features_dict else None,
                json.dumps(rf_features_dict) if rf_features_dict else None,
                ja3_hash,
                ja3_malicious
            )
        )
        conn.commit()
    finally:
        conn.close()

def log_alert(alert:dict):
    conn = sqlite3.connect(ALERT_DB_PATH)
    try:
        conn.execute(
            "INSERT INTO alert_logs "
            "(type, severity, message, timestamp)"
            "VALUES (?, ?, ?, ?)",
            (
                alert['type'],
                alert['severity'],
                alert['message'],
                datetime.now(timezone.utc).isoformat()
            )
        )
        conn.commit()
    finally:
        conn.close()

def write_alert(alert:dict):
    alert['timestamp'] = datetime.now(timezone.utc).isoformat()
    logger.info(json.dumps(alert))

def send_system_notification(alert:dict):
    if sys.platform != 'win32':
        return

    alert_type = alert.get('type', 'ALERT')
    message = alert.get('message', '')
    severity = alert.get('severity', 0)

    title_map = {
        'EXPLICIT_ATTACK_DETECTION': 'Attack Detected',
        'SYSTEMIC_ANOMALY':          'Anomalous Traffic',
        'JA3_MATCH':                 'Malware Fingerprint Matched',
        'MODEL_DRIFT_DETECTION' :    'Model Drift Detected',
        'MODEL_ROLLBACK':            'Model Rolled Back'
    }

    title = title_map.get(alert_type, 'NIDS - Alert')
    body = message

    toast = Toast()
    toast.text_fields = [title, body]
    toast.duration = ToastDuration.Default

    if ICON_PATH.exists():
        toast.AddImage(ToastDisplayImage.fromPath(str(ICON_PATH)))

    toaster.show_toast(toast)

def view_flow_db():
    with sqlite3.connect(FLOW_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        count = conn.execute("SELECT COUNT(*) FROM flow_logs").fetchone()[0]
        print(f"Total logged flows: {count}")

        rows = conn.execute("""
            SELECT timestamp, src_ip, dst_ip, src_port, dst_port, protocol,
                   ae_score, ae_category, rf_score, rf_category, ae_percent, ja3_hash, ja3_malicious
            FROM flow_logs 
            ORDER BY id DESC 
            LIMIT 10
        """).fetchall()

        for row in rows:
            print(dict(row))

def view_alert_db():
    with sqlite3.connect(ALERT_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        count = conn.execute("SELECT COUNT(*) FROM alert_logs").fetchone()[0]
        print(f"Total alerts: {count}")

        rows = conn.execute("""
            SELECT type, severity, message, timestamp
            FROM alert_logs 
            ORDER BY id DESC 
            LIMIT 10
        """).fetchall()

        for row in rows:
            print(dict(row))


if __name__ == '__main__':
    view_flow_db()