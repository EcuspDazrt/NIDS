import pandas as pd
import util.paths as p
import time, torch, json

from datetime import datetime, timezone
from training.ae_train import train_model
from models.definitions.autoencoder import construct_model, get_error
from scripts.build_dataset import create_dataset

from util.thresholds import get_thresholds, calibrate_ae_thresholds
from util.logger import get_logger

LOGGER = get_logger(__name__)
FLOW_THRESHOLD = 1000  # test for 10,000 and 100,000 and 1,000,000 potentially
TIME_WINDOW = 1  # default 7 days


# <---------- Utility Funcs ---------->
def build_records(rows, records):
    for row in rows:
        try:
            records.append(json.loads(row[0]))
        except (json.JSONDecodeError, TypeError):
            LOGGER.error('Could not build validation records')


def log_retrain_event(sample_count, pre_loss, post_loss, duration_seconds, skipped_reason):
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'retrain' if skipped_reason is None else 'retrain_skipped',
        'sample_count': sample_count,
        'pre_loss': None if pre_loss is None else pre_loss,
        'post_loss': None if post_loss is None else post_loss,
        'improvement': None if not pre_loss or not post_loss else round(pre_loss - post_loss, 6),
        'duration_seconds': duration_seconds,
        'skipped_reason': str(skipped_reason),
        'model_path': str(p.AE_WEIGHTS_PATH),
        'backup_path': str(p.BACKUPS_DIR / f'ae_model_backup_{datetime.now(timezone.utc).isoformat()}.pt')
    }

    with open(p.RETRAIN_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def get_normal_fraction(model, validation_path=None):
    if validation_path is not None: # get validation samples from csv file
        validation_samples = pd.read_csv(validation_path)
    else: # build validation samples from sqlite flow logs instead
        from retraining.flow_db_handler import get_validation_samples
        samples = get_validation_samples()
        if not samples:
            return None

        validation_records = []
        build_records(samples, validation_records)
        if len(validation_records) < 50:
            return None
        validation_samples = pd.DataFrame(validation_records)

    x = create_dataset(validation_samples, loader=False)
    model.eval()
    error = get_error(model, x)
    ae_t1 = get_thresholds()['ae'][0]

    normal_fraction = (error < ae_t1).mean()
    return float(normal_fraction)


# <---------- Retrain function itself ---------->
def start_offline_train(defenses=None, flow_ids=None, validation_path=None):
    from retraining.filtering import passes_flow_threshold, passes_time_window, filter_samples, samples_exist
    from retraining.flow_db_handler import get_num_flows, get_days_available, get_ae_samples
    from retraining.drift_check import check_drift

    LOGGER.info('Starting offline training')
    # handle poison defenses
    if defenses is None:
        defenses = {'Isolation Forest': True, 'Temporal Isolation': True, 'Rollback': True}

    temp_iso = defenses.get('Temporal Isolation', False)
    iso_forest = defenses.get('Isolation Forest', False)
    rollback = defenses.get('Rollback', False)

    # load previous model and calculate initial normal fraction first
    previous_model = construct_model(load=True)
    normal_fraction = get_normal_fraction(previous_model, validation_path=validation_path) # validate it against a feature set if inputted
    ae_thresholds = get_thresholds()['ae']

    # attempt model retraining
    num_flows = get_num_flows()
    days_available = get_days_available(temp_iso)
    retrain_samples = get_ae_samples(temp_iso, flow_ids=flow_ids)

    # check if samples fit retrain criteria
    if not passes_flow_threshold(num_flows, additional_msg=' (Fired before filtering)'):
        return None
    if not passes_time_window(days_available):
        return None
    if retrain_samples is None:
        return None

    retrain_records = []
    build_records(retrain_samples, retrain_records)
    if not samples_exist(retrain_records, additional_msg=' (Fired before filtering)'):
        return None
    retrain_samples = pd.DataFrame(retrain_records)
    sample_count = len(retrain_samples)

    # filter samples further if the defense is activated
    if iso_forest:
        retrain_samples, filtered_count = filter_samples(retrain_samples)
        if not passes_flow_threshold(filtered_count, additional_msg=' (Fired after filtering)'):
            return None
        if not samples_exist(retrain_samples, additional_msg=' (Fired after filtering)'):
            return None

    # train model with remaining samples and calculate time
    start_time = time.time()
    pre_loss, post_loss = train_model(load=True, features=retrain_samples)
    duration_seconds = round(time.time() - start_time, 1)

    # log retraining
    LOGGER.info(f'Retraining complete: {sample_count} samples in {duration_seconds} seconds')
    log_retrain_event(sample_count, pre_loss, post_loss, duration_seconds, None)

    # save the backup and evaluate the new model
    save_backup_with_metadata(previous_model, pre_loss, post_loss, normal_fraction, ae_thresholds)
    new_model = construct_model(load=True)

    # monitor model drift if the defense is activated
    drifted, rolled_back = False, False
    if rollback:
        retrained_normal_fraction = get_normal_fraction(new_model, validation_path=validation_path)
        normal_fractions = {'Initial normal': normal_fraction, 'Retrained normal': retrained_normal_fraction} # compute both normal fractions
        drifted, rolled_back = check_drift(normal_fractions=normal_fractions) # use normal fractions to check drift

    calibrate_ae_thresholds(new_model)
    LOGGER.info('Offline training finished')
    return drifted, rolled_back



# <---------- Saving Backups ---------->
def delete_old_backups():
    backups = sorted(p.BACKUPS_DIR.glob('ae_model_backup_*.pt'))
    if len(backups) > 5:
        for old in backups[:-5]:
            old.unlink()
            meta = old.with_suffix('.json')
            if meta.exists():
                meta.unlink()

def save_metadata(meta_path, meta):
    with open(meta_path, 'w') as f:
        json.dump(meta, f)


def save_backup_with_metadata(model, pre_loss, post_loss, normal_fraction, ae_thresholds):
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_path = p.BACKUPS_DIR / f'ae_model_backup_{timestamp}.pt'
    meta_path = p.BACKUPS_DIR / f'ae_model_backup_{timestamp}.json'

    meta = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pre_loss': pre_loss,
        'post_loss': post_loss,
        'normal_fraction': normal_fraction,
        'ae_thresholds': ae_thresholds,
        'path': str(backup_path)
    }

    torch.save(model.state_dict(), backup_path) # save model itself
    save_metadata(meta_path, meta)
    delete_old_backups()

    return backup_path


if __name__ == '__main__':
    calibrate_ae_thresholds(construct_model(load=True))
