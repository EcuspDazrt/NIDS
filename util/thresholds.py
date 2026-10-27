import numpy as np
import util.paths as p
import torch, json

from util.feature_retrieval import get_ae_testing, get_ae_features_benign_testing, get_rf_features_testing, get_rf_labels_testing
from sklearn.metrics import precision_recall_curve
from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model as construct_ae, get_error
from models.definitions.random_forest import construct_model as construct_rf

from util.logger import get_logger
LOGGER = get_logger(__name__)


# <---------- Dependency retrieval ---------->
def get_thresholds():
    with open(p.THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    return thresholds


# <---------- Threshold Calculations ---------->
def calculate_ae_thresholds(thresholds, f1_scores, err):
    ae_bin = None
    if thresholds is not None and f1_scores is not None:
        ae_bin = thresholds[np.argmax(f1_scores)]

    t1 = np.percentile(err, 90)
    t2 = np.percentile(err, 95)
    t3 = np.percentile(err, 99)
    ae_max = np.percentile(err, 99.9)

    return float(ae_bin), [float(t1), float(t2), float(t3), float(ae_max)]


def calculate_rf_thresholds(pr_thresholds, f1_scores, proba):
    rf_bin = pr_thresholds[np.argmax(f1_scores)]
    t1 = np.percentile(proba, 90)
    t2 = np.percentile(proba, 95)
    t3 = np.percentile(proba, 99)

    return float(rf_bin), [float(t1), float(t2), float(t3)]


# <---------- Calibration & Recalibration ---------->
def replace_ae_thresholds(ae_binary, ae_thresholds):
    with open(p.THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    thresholds['ae_binary'] = ae_binary
    thresholds['ae'] = ae_thresholds
    with open(p.THRESHOLDS_PATH, 'w') as f:
        json.dump(thresholds, f)


def dump_thresholds(thresholds):
    with open(p.THRESHOLDS_PATH, 'w') as f:
        json.dump(thresholds, f)


def calibrate_ae_thresholds(ae=None):
    LOGGER.info('[START] AE threshold calibration')
    if ae is None:
        ae = construct_ae(load=True)
        ae.eval()

    testing_features = get_ae_testing()
    ae_benign_features = create_dataset(testing_features['ae_testing_benign'], loader=False)
    ae_malicious_features = create_dataset(testing_features['ae_testing_malicious'], loader=False)

    with torch.no_grad():
        error_benign = get_error(ae, ae_benign_features)
        error_malicious = get_error(ae, ae_malicious_features)
    errors_combined = np.concatenate([error_benign, error_malicious])
    labels = np.array([0] * len(error_benign) + [1] * len(error_malicious))

    precision, recall, thresholds = precision_recall_curve(labels, errors_combined)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)

    LOGGER.info('[COMPLETE] AE threshold calibration')
    return calculate_ae_thresholds(thresholds, f1_scores, error_benign)


def calibrate_rf_thresholds():
    LOGGER.info('[START] RF threshold calibration')
    rf = construct_rf()

    rf_features = get_rf_features_testing()
    rf_labels = get_rf_labels_testing()

    proba = rf.predict_proba(rf_features)[:, 1]
    precision, recall, pr_thresholds = precision_recall_curve(rf_labels, proba)
    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-8)

    LOGGER.info('[COMPLETE] RF threshold calibration')
    return calculate_rf_thresholds(pr_thresholds, f1_scores, proba)


def calibrate_thresholds():
    LOGGER.info('[START] threshold calibration')
    ae_binary_threshold, ae_category_thresholds = calibrate_ae_thresholds()
    rf_binary_threshold, rf_category_thresholds = calibrate_rf_thresholds()

    thresholds = {'rf': rf_category_thresholds,
                  'rf_binary': rf_binary_threshold,
                  'ae': ae_category_thresholds,
                  'ae_binary': ae_binary_threshold,
                  }

    dump_thresholds(thresholds)
    LOGGER.info(f'[COMPLETE] threshold calibration: {json.dumps(thresholds, indent=2)}')


if __name__ == "__main__":
    calibrate_thresholds()
