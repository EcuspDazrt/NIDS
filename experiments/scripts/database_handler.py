import sqlite3, json, socket
import experiments.scripts.paths as p
from experiments.structs.ae_feature_list import AE_FEATURES
from datetime import datetime, timezone


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



def log_experiment(description, experiment_id, results):
    with sqlite3.connect(p.EXPERIMENT_DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                description   TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                results       TEXT NOT NULL
                )
            ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_experiment ON experiments(experiment_id)
        ''')
        conn.execute(
            "INSERT INTO experiments "
            "(description, experiment_id, results) "
            "VALUES (?, ?, ?)",
            (
                description,
                experiment_id,
                json.dumps(results) if results is not None else None
            )
        )


def view_experiment_table():
    with sqlite3.connect(p.EXPERIMENT_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        count = conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
        print(f"Total logged experiments: {count}")

        rows = conn.execute("""
            SELECT description, experiment_id, results
            FROM experiments 
            ORDER BY id DESC 
            LIMIT 10
        """).fetchall()

        for row in rows:
            try:
                data = dict(row)
                data['results'] = json.loads(data['results'])

                print(json.dumps(data, indent=2))
            except:
                print('Did not work.')


# ------- Experimental Database Handling (used as a helper function for experiments) -------
def init_experimental_db(flow_db_path):
    flow_db_path.parent.mkdir(exist_ok=True)

    with sqlite3.connect(flow_db_path) as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS flow_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT NOT NULL,
            ae_features   TEXT,
            rf_features   TEXT,
            rf_category   INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON flow_logs(timestamp)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_rf_category ON flow_logs(rf_category)
        ''')


def log_flow(flow_db_path, rf_category=0, ae_features_dict=None, rf_features_dict=None):
    conn = sqlite3.connect(flow_db_path)

    if rf_features_dict is not None:
        if ae_features_dict:
            ae_features_dict['Source IP'] = ip_to_str(ae_features_dict['Source IP'])
            ae_features_dict['Destination IP'] = ip_to_str(ae_features_dict['Destination IP'])
        try:
            rf_features_dict['Source IP'] = ip_to_str(rf_features_dict['Source IP'])
            rf_features_dict['Destination IP'] = ip_to_str(rf_features_dict['Destination IP'])
            conn.execute(
                "INSERT INTO flow_logs "
                "(timestamp, ae_features, rf_features, rf_category) "
                "VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(ae_features_dict) if ae_features_dict else None,
                    json.dumps(rf_features_dict) if rf_features_dict else None,
                    rf_category
                )
            )
            conn.commit()
        finally:
            conn.close()
    else:
        try:
            conn.execute(
                "INSERT INTO flow_logs "
                "(timestamp, ae_features, rf_category) "
                "VALUES (?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(ae_features_dict) if ae_features_dict else None,
                    rf_category
                )
            )
            conn.commit()
        finally:
            conn.close()


def inject_poisoned_flows(db_path, poisoned_df):
    with sqlite3.connect(db_path) as conn:
        for _, row in poisoned_df.iterrows():
            features = row[AE_FEATURES].to_dict()
            conn.execute(
                "INSERT INTO flow_logs (timestamp, ae_features, rf_category) VALUES (?, ?, ?)",
                (row['timestamp'], json.dumps(features), 0)
            )


if __name__ == '__main__':
    view_experiment_table()
