import sqlite3
import json
from datetime import datetime, timezone

from training.ae_train import train_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

FLOW_DB_PATH = BASE_DIR.parent / 'data' / 'nids_flows.db'
OFFLINE_LOG_PATH = BASE_DIR.parent / 'data' / 'nids_retraining.log'
FLOW_THRESHOLD = 10000
# test for 10,000 and 100,000 and 1,000,000 potentially

def log_retrain_event(training_information):
    sample_count, pre_loss, post_loss, duration_seconds, skipped_reason = training_information

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'retrain' if skipped_reason is None else 'retrain_skipped',
        'sample_count': sample_count,
        'pre_loss': pre_loss,
        'post_loss': post_loss,
        'improve_ment': round(pre_loss - post_loss, 6) if pre_loss and post_loss else None,
        'duration_seconds': duration_seconds,
        'skipped_reason': skipped_reason,
        'model_path': BASE_DIR.parent/'models'/'artifacts'/'ae_model.pt',
        'backup_path': BASE_DIR.parent/'models'/'artifacts'/f'ae_model_backup_{datetime.now(timezone.utc).isoformat()}.pt'
    }

    with open(OFFLINE_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def start_offline_train():
    with sqlite3.connect(FLOW_DB_PATH) as conn:
        total = conn.execute('''
            SELECT count(*) FROM flow_logs
        ''').fetchone()[0]

        excluded = conn.execute('''
            SELECT count(*) FROM flow_logs
            WHERE timestamp < datetime('now', '-24 hours')
            AND timestamp > datetime('now', '-7 days')
        ''').fetchone()[0]

        recent = conn.execute('''
            SELECT count(*) FROM flow_logs
            WHERE timestamp > datetime('now', '-24 hours')
        ''').fetchone()[0]

        try:
            samples = conn.execute('''
                SELECT ae_features, rf_features FROM flow_logs
                WHERE rf_category = 0
                AND timestamp < datetime('now', '-24 hours')
                AND timestamp > datetime('now', '-7 days')
            ''').fetchone()[0]
        except:
            print('Could not find any available samples')

        print(f'Total flows counted: {total}')
        print(f'Recent flows counted: {recent}')
        print(f'Temporally isolated flows counted: {excluded}')

        training_information = train_model(load=True, epochs=20, features=samples)
        log_retrain_event(training_information)

def check_db():
    with sqlite3.connect(FLOW_DB_PATH) as conn:
        total = conn.execute('''
            SELECT count(*) FROM flow_logs
        ''').fetchone()[0]

        time_overflow = conn.execute('''
            SELECT count(*) FROM flow_logs
            WHERE timestamp > datetime('now', '-7 days')
        ''').fetchone()[0]

        if time_overflow and total >= FLOW_THRESHOLD:
            start_offline_train()

if __name__ == '__main__':
    start_offline_train()