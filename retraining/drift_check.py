import sqlite3, json, shutil
import util.paths as p

from datetime import datetime, timezone
from pathlib import Path

from util.thresholds import replace_ae_thresholds
from util.logger import get_logger

from retraining.flow_db_handler import get_drift_check_samples

LOGGER = get_logger(__name__)
NORMAL_TIER_FLOOR = 0.50  # shift to find what the initial normal fraction is
HISTORICAL_MULTIPLIER = 0.7  # higher means more sensitivity


# <---------- External Signals ---------->
def write_drift_entry(entry):
    with open(p.DRIFT_CHECK_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def write_rollback_entry(entry):
    with open(p.RETRAIN_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def signal_alert(alert_engine, drift_reason):
    LOGGER.info(f'Drift detected: {drift_reason}')

    try:
        alert_engine.signal_drift(drift_reason)
    except (AttributeError, TypeError):
        LOGGER.error('No alert engine provided')
    except Exception:
        LOGGER.exception('Was not able to send an alert')



# <---------- Drift check utility funcs ---------->
def to_category_fractions(samples):
    # sample[0] is the category, and sample[1] is the number of samples in that category
    total = sum(r[1] for r in samples)
    if total == 0:
        return {}
    return {sample[0]: sample[1] / total for sample in samples}


def populate_entry(entry, recent_normal, historical_normal):
    if recent_normal < NORMAL_TIER_FLOOR:
        entry['drift_detected'] = True
        entry['reason'] = f'normal tier dropped to {recent_normal:.1%} (floor: {NORMAL_TIER_FLOOR:.0%})'

    if historical_normal > 0 and recent_normal < historical_normal * HISTORICAL_MULTIPLIER:
        entry['drift_detected'] = True
        entry['reason'] = (
            f'normal tier dropped {(historical_normal - recent_normal):.1%} '
            f'below historical average ({historical_normal:.1%} -> {recent_normal:.1%})'
        )


def calculate_normal_fractions():
    recent_samples, historical_samples = get_drift_check_samples()
    if not recent_samples or not historical_samples:
        LOGGER.warning('Skipped drift check: No recent or historical data found')
        return None

    recent_fracs = to_category_fractions(recent_samples)
    historical_fracs = to_category_fractions(historical_samples)

    # get the fraction of samples in which the auto-encoder did NOT detect it as malicious whatsoever
    recent_normal = recent_fracs.get(0, 0.0)
    historical_normal = historical_fracs.get(0, 0.0)

    return {'Initial normal': historical_normal, 'Retrained normal': recent_normal}



# <---------- Drift check itself ---------->
def check_drift(alert_engine=None, normal_fractions=None):
    LOGGER.info('Drift check began')
    if normal_fractions is None:
        normal_fractions = calculate_normal_fractions()

    historical_normal = normal_fractions.get('Initial normal', 0)
    recent_normal = normal_fractions.get('Retrained normal', 0)

    drift_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'drift_check',
        'recent_normal_fraction': round(recent_normal, 3),
        'historical_normal_fraction': round(historical_normal, 3),
        'drift_detected': False,
        'reason': None
    }

    populate_entry(drift_entry, recent_normal, historical_normal)
    write_drift_entry(drift_entry)

    drift_detected = drift_entry['drift_detected']
    drift_reason = drift_entry['reason']

    if not drift_detected:
        LOGGER.info('Drift check finished')
        return False, False
    signal_alert(alert_engine, drift_reason)
    rolled_back = try_rollback()

    LOGGER.info('Drift check finished')
    return True, rolled_back


# <---------- Rollback Funcs ---------->
def get_metadata_paths():
    metas = sorted(p.BACKUPS_DIR.glob('ae_model_backup_*.json'))
    if not metas:
        LOGGER.warning('No backups available for rollback')
        return None
    return metas


def build_rollback_candidates(metas, candidates):
    for meta_path in metas:
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            model_path = Path(meta['path'])
            if model_path.exists():
                candidates.append(meta)
        except Exception:
            LOGGER.exception('Error reading model metadata')

    if not candidates:
        LOGGER.warning('No valid backup candidates found')

def rollback_model(best_rollback_candidate):
    LOGGER.info(f'Rolling back to {best_rollback_candidate['timestamp']}'
                f'(normal_fraction: {best_rollback_candidate['normal_fraction']:.1%},'
                f'loss: {best_rollback_candidate['post_loss']:.6f})')

    # rollback model and thresholds
    shutil.copy(best_rollback_candidate['path'], p.AE_WEIGHTS_PATH)
    replace_ae_thresholds(best_rollback_candidate['ae_thresholds'])

    # log rollback
    rollback_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'rollback',
        'rolled_back_to': best_rollback_candidate['timestamp'],
        'normal_fraction': best_rollback_candidate['normal_fraction'],
        'reason': 'drift detected'
    }

    write_rollback_entry(rollback_entry)

def try_rollback() -> bool:  # returns whether the rollback was successful
    LOGGER.info('Rollback began')
    metadata_paths = get_metadata_paths()
    if not metadata_paths:
        return False

    rollback_candidates = []
    build_rollback_candidates(metadata_paths, rollback_candidates)
    if not rollback_candidates:
        return False

    best_rollback_candidate = sorted(rollback_candidates, key=lambda x: x.get('normal_fraction', 0), reverse=True)[0]
    rollback_model(best_rollback_candidate)
    return True
