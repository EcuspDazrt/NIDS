from retraining.retrain_ae import log_retrain_event
from models.definitions.isolation_forest import iso_forest_filter

from util.logger import get_logger
LOGGER = get_logger(__name__)

def passes_flow_threshold(num_flows, additional_msg=''):
    from retraining.retrain_ae import FLOW_THRESHOLD
    if num_flows < FLOW_THRESHOLD:
        message = f'insufficient number of flows: {num_flows} < {FLOW_THRESHOLD}{additional_msg}'
        log_retrain_event(0, None, None, 0, message)
        LOGGER.warning(message)
        return False
    return True


def passes_time_window(days_available, additional_msg=''):
    from retraining.retrain_ae import TIME_WINDOW
    if days_available < TIME_WINDOW:
        message = f'insufficient time window: {days_available} < {TIME_WINDOW}{additional_msg}'
        log_retrain_event(0, None, None, 0, message)
        LOGGER.warning(message)
        return False
    return True


def samples_exist(records, additional_msg=''):
    if not records:
        message = f'no eligible samples after filtering{additional_msg}'
        log_retrain_event(0, None, None, 0, message)
        LOGGER.warning(message)
        return False
    return True

def filter_samples(samples):
    original_count = len(samples)
    iso_mask = iso_forest_filter(samples)
    samples = samples[iso_mask]
    filtered_count = len(samples)

    LOGGER.info(f'Isolation forest removed {original_count - filtered_count} suspicious flows'
          f'{(original_count - filtered_count) / original_count:.1%}')

    return samples, filtered_count