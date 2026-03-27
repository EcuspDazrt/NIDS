import sqlite3
import json
import pandas as pd
import numpy as np
import time
import torch
import shutil
from datetime import datetime, timezone

from training.ae_train import train_model
from models.definitions.isolation_forest import iso_forest_filter

from pathlib import Path
BASE_DIR = Path(__file__).parent

FLOW_DB_PATH = BASE_DIR.parent / 'data' / 'nids_flows.db'
OFFLINE_LOG_PATH = BASE_DIR.parent / 'data' / 'nids_retraining.log'
DRIFT_LOG_PATH = BASE_DIR.parent / 'data' / 'nids_drift_check.log'
THRESHOLDS_PATH = BASE_DIR.parent / 'models' / 'artifacts' / 'thresholds.json'

NORMAL_TIER_FLOOR = 0.50 # shift to find what the initial normal fraction is
HISTORICAL_MULTIPLIER = 0.7 # higher means more sensitivity
FLOW_THRESHOLD = 100000 # test for 10,000 and 100,000 and 1,000,000 potentially
TIME_WINDOW = 7 # days

def log_retrain_event(sample_count, pre_loss, post_loss, duration_seconds, skipped_reason):
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'retrain' if skipped_reason is None else 'retrain_skipped',
        'sample_count': sample_count,
        'pre_loss': pre_loss,
        'post_loss': post_loss,
        'improvement': None if not pre_loss or not post_loss else round(pre_loss - post_loss, 6),
        'duration_seconds': duration_seconds,
        'skipped_reason': str(skipped_reason),
        'model_path': str(BASE_DIR.parent/'models'/'artifacts'/'ae_model.pt'),
        'backup_path': str(BASE_DIR.parent/'models'/'artifacts'/f'ae_model_backup_{datetime.now(timezone.utc).isoformat()}.pt')
    }

    with open(OFFLINE_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def try_retrain(defenses=None):
    if defenses is None:
        defenses = {'Isolation Forest':True, 'Temporal Isolation':True, 'Rollback':True}

    with sqlite3.connect(FLOW_DB_PATH) as conn:
        total = conn.execute('''
            SELECT count(*) FROM flow_logs
        ''').fetchone()[0]

        time_overflow = conn.execute('''
            SELECT count(*) FROM flow_logs
            WHERE timestamp > datetime('now', '-7 days')
        ''').fetchone()[0]

        if time_overflow and total >= FLOW_THRESHOLD:
            start_offline_train(defenses=defenses)
        else:
            print('Ineligible for retraining')

def start_offline_train(defenses=None):
    if defenses is None:
        defenses = {'Isolation Forest':True, 'Temporal Isolation':True, 'Rollback':True}

    # loading previous model and calculating initial normal fraction first
    from models.definitions.autoencoder import construct_model
    previous_model = construct_model(load=True)
    normal_fraction = evaluate_retrained_model(previous_model)
    # calculate previous model's thresholds
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    ae_thresholds = (thresholds['ae'], thresholds['ae_max'])

    # attempt model retraining
    with sqlite3.connect(FLOW_DB_PATH) as conn:
        total = conn.execute('''
            SELECT count(*) FROM flow_logs
        ''').fetchone()[0]

        if defenses.get('Temporal Isolation', False):
            days_available = conn.execute('''
                SELECT COUNT(DISTINCT date(timestamp)) FROM flow_logs
                WHERE timestamp < datetime('now', '-24 hours')
                AND timestamp > datetime('now', '-7 days')
            ''').fetchone()[0]

            try:
                rows = conn.execute('''
                    SELECT ae_features FROM flow_logs
                    WHERE rf_category = 0
                    AND timestamp < datetime('now', '-24 hours')
                    AND timestamp > datetime('now', '-7 days')
                ''').fetchall()

            except:
                message = 'no eligible samples after filtering (fired from query execution with temporal isolation)'
                log_retrain_event(0, None, None, 0, message)
                print(message)
                return
        else:
            days_available = conn.execute('''
                SELECT COUNT(DISTINCT date(timestamp)) FROM flow_logs
                WHERE timestamp > datetime('now', '-7 days')
            ''').fetchone()[0]

            try:
                rows = conn.execute('''
                    SELECT ae_features FROM flow_logs
                    WHERE rf_category = 0
                    AND timestamp > datetime('now', '-7 days')
                ''').fetchall()

            except:
                message = 'no eligible samples after filtering (fired after query execution without temporal isolation)'
                log_retrain_event(0, None, None, 0, message)
                print(message)
                return

        if total < FLOW_THRESHOLD:
            message = f'insufficient total flows: {total} < {FLOW_THRESHOLD} (fired from total)'
            log_retrain_event(0, None, None, 0, message)
            print(message)
            return

        if days_available < TIME_WINDOW:
            message = f'insufficient time window: {days_available} < {TIME_WINDOW}'
            log_retrain_event(0, None, None, 0, message)
            print(message)
            return

        records = []
        for row in rows:
            try:
                records.append(json.loads(row[0]))
            except (json.JSONDecodeError, TypeError) as e:
                print(f'Error building records: {e}')
                continue

        if not records:
            message = 'no eligible samples after filtering (fired after record building)'
            log_retrain_event(0, None, None, 0, message)
            print(message)
            return

        sample_count = len(records)
        if sample_count < FLOW_THRESHOLD:
            message = 'insufficient total samples (fired after record building)'
            log_retrain_event(0, None, None, 0, message)
            print(message)
            return

        features = pd.DataFrame(records)

        if defenses.get('Isolation Forest', False):
            original_count = len(features)
            iso_mask = iso_forest_filter(features)
            features = features[iso_mask]
            filtered_count = len(features)

            print(f'Isolation forest removed {original_count - filtered_count} suspicious flows'
                  f'{(original_count - filtered_count)/original_count:.1%}')

            if features.empty:
                message = 'no eligible samples after filtering (fired after isolation forest mask)'
                log_retrain_event(0, None, None, 0, message)
                print(message)
                return

            if filtered_count < FLOW_THRESHOLD:
                message = 'insufficient total samples (fired after isolation forest mask)'
                log_retrain_event(0, None, None, 0, message)
                print(message)
                return

        start_time = time.time()
        pre_loss, post_loss = train_model(load=True, features=features)
        duration_seconds = round(time.time() - start_time, 1)

        log_retrain_event(sample_count, pre_loss, post_loss, duration_seconds, None)
        print(f'Retraining complete: {sample_count} samples in {duration_seconds} seconds')

        save_backup_with_metadata(previous_model, pre_loss, post_loss, normal_fraction, ae_thresholds)

        new_model = construct_model(load=True)
        recalibrate_ae_thresholds(new_model)

def recalibrate_ae_thresholds(ae):
    from scripts.build_dataset import create_dataset

    features_benign = pd.read_csv( BASE_DIR.parent/'datasets'/'processed'/'ae_testing_benign.csv', low_memory = False)
    x_benign = create_dataset(features_benign, loader=False)

    ae.eval()
    with torch.no_grad():
        recon = ae(x_benign)
        error_benign = ((x_benign - recon)**2).mean(dim=1).numpy()

    ae_t1 = float(np.percentile(error_benign, 90))
    ae_t2 = float(np.percentile(error_benign, 95))
    ae_t3 = float(np.percentile(error_benign, 99))
    ae_max = float(np.percentile(error_benign, 99.9))

    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    thresholds['ae'] = [ae_t1, ae_t2, ae_t3]
    thresholds['ae_max'] = ae_max
    with open(THRESHOLDS_PATH, 'w') as f:
        json.dump(thresholds, f)

    print(f'Recalibrated AE tiers: {ae_t1:.4f}, {ae_t2:.4f}, {ae_t3:.4f}')
    print(f'Recalibrated AE max: {ae_max:.4f}')


def evaluate_retrained_model(model):
    from scripts.build_dataset import create_dataset

    with sqlite3.connect(FLOW_DB_PATH) as conn:
        rows = conn.execute('''
            SELECT ae_features FROM flow_logs
            WHERE rf_category = 0
            AND ae_features IS NOT NULL
            AND timestamp > datetime('now', '-24 hours')
            LIMIT 500
        ''').fetchall()

    if not rows:
        return None

    records = []
    for row in rows:
        try:
            records.append(json.loads(row[0]))
        except Exception as e:
            print(f'Error loading row: {e}')

    if len(records) < 50:
        return None

    df = pd.DataFrame(records)
    x = create_dataset(df, loader=False)

    model.eval()
    with torch.no_grad():
        recon = model(x)
        errors = ((x - recon) ** 2).mean(dim=1).numpy()

    with open(BASE_DIR.parent / 'models' / 'artifacts' / 'thresholds.json') as f:
        t = json.load(f)
    ae_t1 = t['ae'][0]

    normal_fraction = (errors < ae_t1).mean()
    return float(normal_fraction)

def rollback_ae(): # returns whether the rollback was successful
    artifacts = BASE_DIR.parent / 'models' / 'artifacts'
    backups_dir = artifacts / 'retraining_backups'

    metas = sorted(backups_dir.glob('ae_model_backup_*.json'))
    if not metas:
        print('No backups available for rollback')
        return False

    candidates = []
    for meta_path in metas:
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            model_path = Path(meta['path'])
            if model_path.exists():
                candidates.append(meta)
        except Exception as e:
            print(f'Error reading model metadata: {e}')

    if not candidates:
        print('No valid backup candidates found')
        return False

    best = sorted(candidates, key=lambda x: x.get('normal_fraction', 0), reverse=True)[0]

    print(f'Rolling back to {best["timestamp"]}'
          f'(normal_fraction: {best["normal_fraction"]:.1%},'
          f'loss: {best["post_loss"]:.6f})')

    shutil.copy(best['path'], artifacts / 'ae_model.pt')

    # rollback thresholds with the model itself
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    thresholds['ae'] = best['ae_category_thresholds']
    thresholds['ae_max'] = best['ae_max']

    with open(THRESHOLDS_PATH, 'w') as f:
        json.dump(thresholds, f)

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'rollback',
        'rolled_back_to': best["timestamp"],
        'normal_fraction': best["normal_fraction"],
        'reason': 'drift detected'
    }
    with open(OFFLINE_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    return True

def save_backup_with_metadata(model, pre_loss, post_loss, normal_fraction, ae_thresholds):
    artifacts = BASE_DIR.parent / 'models' / 'artifacts'
    backups_dir = artifacts / 'retraining_backups'
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    Path.mkdir(backups_dir, exist_ok=True)

    backup_path = backups_dir / f'ae_model_backup_{timestamp}.pt'
    meta_path = backups_dir / f'ae_model_backup_{timestamp}.json'

    torch.save(model.state_dict(), backup_path)

    ae_category_thresholds, ae_max = ae_thresholds

    meta = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pre_loss': pre_loss,
        'post_loss': post_loss,
        'normal_fraction': normal_fraction,
        'ae_category_thresholds': ae_category_thresholds,
        'ae_max': ae_max,
        'path': str(backup_path)
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f)

    backups = sorted(backups_dir.glob('ae_model_backup_*.pt'))
    if len(backups) > 5:
        for old in backups[:-5]:
            old.unlink()
            meta = old.with_suffix('.json')
            if meta.exists():
                meta.unlink()

    return backup_path

def check_drift(alert_engine=None):
    with sqlite3.connect(FLOW_DB_PATH) as conn:

        recent = conn.execute('''
            SELECT ae_category, COUNT(*) as count
            FROM flow_logs
            WHERE timestamp > datetime('now', '-2 hours')
            GROUP BY ae_category
        ''').fetchall()

        historical = conn.execute('''
            SELECT ae_category, COUNT(*) as count
            FROM flow_logs
            WHERE timestamp > datetime('now', '-7 days')
            AND timestamp < datetime('now', '-2 hours')
            GROUP BY ae_category
        ''').fetchall()

    if not recent or not historical:
        print('Skipped drift check: No recent or historical data found')
        return False

    def tier_fractions(rows):
        total = sum(r[1] for r in rows)
        if total == 0:
            return {}
        return {r[0]: r[1] / total for r in rows}

    recent_fracs = tier_fractions(recent)
    historical_fracs = tier_fractions(historical)

    recent_normal = recent_fracs.get(0, 0.0)
    historical_normal = historical_fracs.get(0, 0.0)

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'drift_check',
        'recent_normal_fraction': round(recent_normal, 3),
        'historical_normal_fraction': round(historical_normal, 3),
        'drift_detected': False,
        'reason': None
    }

    if recent_normal < NORMAL_TIER_FLOOR:
        entry['drift_detected'] = True
        entry['reason'] = f'normal tier dropped to {recent_normal:.1%} (floor: {NORMAL_TIER_FLOOR:.0%})'

    if historical_normal > 0 and recent_normal < historical_normal * HISTORICAL_MULTIPLIER:
        entry['drift_detected'] = True
        entry['reason'] = (
            f'normal tier dropped {(historical_normal - recent_normal):.1%} '
            f'below historical average ({historical_normal:.1%} -> {recent_normal:.1%})'
        )

    with open(DRIFT_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    if entry['drift_detected']:
        print(f'drift detected: {entry['reason']}')
        if alert_engine:
            alert_engine.signal_drift(entry['reason'])
        return True

    return False

if __name__ == '__main__':
    from models.definitions.autoencoder import construct_model
    recalibrate_ae_thresholds(construct_model(load=True))