import sqlite3
import json
import socket
from datetime import datetime

from pathlib import Path
DB_PATH = Path(__file__).parent.parent / 'data' / 'nids_logs.db'

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
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS flow_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            src_ip      TEXT,
            dst_ip      TEXT,
            src_port    INTEGER,
            dst_port    INTEGER,
            protocol    INTEGER,
            ae_score    REAL,
            ae_category INTEGER,
            rf_score    REAL,
            rf_category INTEGER,
            ae_percent  INTEGER,
            features    TEXT
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON flow_logs(timestamp)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_rf_category ON flow_logs(rf_category)
        ''')

def log_flow(flow, ae_percent, ae_category, rf_category, ae_score, rf_score, features_dict=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO flow_logs "
            "(timestamp, src_ip, dst_ip, src_port, dst_port, protocol, "
            "ae_score, ae_category, rf_score, rf_category, ae_percent, features) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
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
                json.dumps(features_dict) if features_dict else None
            )
        )
        conn.commit()
    finally:
        conn.close()


def view_db():
    import sqlite3
    from pathlib import Path
    BASE_DIR = Path(__file__).parent

    DB_PATH = Path(BASE_DIR.parent/'data'/'nids_logs.db')  # adjust to your actual path

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        # how many rows total
        count = conn.execute("SELECT COUNT(*) FROM flow_logs").fetchone()[0]
        print(f"Total logged flows: {count}")

        # last 10 entries
        rows = conn.execute("""
            SELECT timestamp, src_ip, dst_ip, src_port, dst_port,
                   ae_percent, ae_category, rf_category
            FROM flow_logs 
            ORDER BY id DESC 
            LIMIT 10
        """).fetchall()

        for row in rows:
            print(dict(row))


if __name__ == '__main__':
    view_db()