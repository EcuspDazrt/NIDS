import pandas as pd
import numpy as np
import torch
import json

from sklearn.metrics import precision_recall_curve

from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model as construct_ae
from models.definitions.random_forest import construct_model as construct_rf

from pathlib import Path
BASE_DIR = Path(__file__).parent
parent_dir = BASE_DIR.parent / 'datasets' / 'processed'

ae_benign_path = parent_dir / 'ae_testing_benign.csv'
ae_malicious_path = parent_dir / 'ae_testing_malicious.csv'
rf_path = parent_dir / 'rf_testing.csv'
rf_labels_path = parent_dir / 'rf_testing_labels.csv'

thresholds_path = BASE_DIR.parent /'models'/'artifacts'/'thresholds.json'

def get_ae_features():
    features_benign = pd.read_csv(ae_benign_path, low_memory=False)
    x_benign = create_dataset(features_benign, loader=False)
    features_malicious = pd.read_csv(ae_malicious_path, low_memory=False)
    x_malicious = create_dataset(features_malicious, loader=False)

    return x_benign, x_malicious

def get_ae_errors(ae, x_ben, x_mal):
    recon_ben = ae(x_ben)
    error_ben = ((x_ben - recon_ben) ** 2).mean(dim=1).numpy()
    recon_mal = ae(x_mal)
    error_mal = ((x_mal - recon_mal) ** 2).mean(dim=1).numpy()

    return error_ben, error_mal

def calculate_ae_thresholds(thresholds, f1_scores, err):
    ae_bin = thresholds[np.argmax(f1_scores)]
    t1 = np.percentile(err, 90)
    t2 = np.percentile(err, 95)
    t3 = np.percentile(err, 99)
    ae_max = np.percentile(err, 99.9)

    return ae_bin, t1, t2, t3, ae_max

def calculate_rf_thresholds(pr_thresholds, f1_scores, proba):
    rf_bin = pr_thresholds[np.argmax(f1_scores)]
    t1 = np.percentile(proba, 90)
    t2 = np.percentile(proba, 95)
    t3 = np.percentile(proba, 99)

    return rf_bin, t1, t2, t3

def check_dataset():
    if not ae_benign_path.exists() or not ae_malicious_path.exists() or not rf_path.exists() or not rf_labels_path.exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

def calibrate_thresholds():
    print('Calibrating thresholds...')
    ae = construct_ae(load=True)
    ae.eval()
    check_dataset()
    x_benign, x_malicious = get_ae_features()

    with torch.no_grad():
        error_benign, error_malicious = get_ae_errors(ae, x_benign, x_malicious)
        errors_combined = np.concatenate([error_benign, error_malicious])
        labels = np.array([0] * len(error_benign) + [1] * len(error_malicious))

        precision, recall, thresholds = precision_recall_curve(labels, errors_combined) # calculate metrics
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)

        ae_binary_threshold, ae_t1, ae_t2, ae_t3, ae_max_threshold = calculate_ae_thresholds(thresholds, f1_scores, error_benign) # retrieve thresholds from metrics

    print(f'AE tiers: {ae_t1:.4f}, {ae_t2:.4f}, {ae_t3:.4f}')
    print(f'AE max threshold: {ae_max_threshold:.4f}')
    print(f'AE binary threshold: {ae_binary_threshold:.4f}')

    # begin calculating random forest thresholds
    rf = construct_rf()

    x_test = pd.read_csv(rf_path)
    y_test = pd.read_csv(rf_labels_path)

    proba = rf.predict_proba(x_test)[:,1] # calculate metrics on random forest
    precision, recall, pr_thresholds = precision_recall_curve(y_test, proba)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)

    rf_binary_threshold, t1_rf, t2_rf, t3_rf = calculate_rf_thresholds(pr_thresholds, f1_scores, proba)
    print(f'RF binary threshold: {rf_binary_threshold:.4f}')
    print(f'RF tiers: {t1_rf:.4f}, {t2_rf:.4f}, {t3_rf:.4f}')

    thresholds = {'rf': [float(t1_rf), float(t2_rf), float(t3_rf)],
                  'rf_binary': float(rf_binary_threshold),
                  'ae': [float(ae_t1), float(ae_t2), float(ae_t3)],
                  'ae_binary': float(ae_binary_threshold),
                  'ae_max': float(ae_max_threshold)
                  }

    with open(thresholds_path, 'w') as f:
        json.dump(thresholds, f)

if __name__ == "__main__":
    calibrate_thresholds()