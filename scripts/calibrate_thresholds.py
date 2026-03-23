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

def calibrate_thresholds():
    print('Calibrating thresholds...')
    ae = construct_ae(load=True)
    ae.eval()

    if not Path(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv').exists() or not Path(BASE_DIR.parent/ 'datasets' / 'processed' / 'ae_testing_malicious.csv').exists()\
    or not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv').exists() or not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    features_benign = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv', low_memory=False)
    x_benign = create_dataset(features_benign, loader=False)
    features_malicious = pd.read_csv(BASE_DIR.parent/ 'datasets' / 'processed' / 'ae_testing_malicious.csv', low_memory=False)
    x_malicious = create_dataset(features_malicious, loader=False)
    with torch.no_grad():
        recon_benign = ae(x_benign)
        error_benign = ((x_benign - recon_benign) ** 2).mean(dim=1).numpy()
        recon_malicious = ae(x_malicious)
        error_malicious = ((x_malicious - recon_malicious) ** 2).mean(dim=1).numpy()

        errors_combined = np.concatenate([error_benign, error_malicious])
        labels = np.array([0] * len(error_benign) + [1] * len(error_malicious))

        precision, recall, thresholds = precision_recall_curve(labels, errors_combined)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        ae_binary_threshold = thresholds[np.argmax(f1_scores)]

        ae_t1 = np.percentile(error_benign, 90)
        ae_t2 = np.percentile(error_benign, 95)
        ae_t3 = np.percentile(error_benign, 99)
        ae_max_threshold = np.percentile(error_benign, 99.9)

    print(f'AE tiers: {ae_t1:.4f}, {ae_t2:.4f}, {ae_t3:.4f}')
    print(f'AE max threshold: {ae_max_threshold:.4f}')
    print(f'AE binary threshold: {ae_binary_threshold:.4f}')

    rf = construct_rf()

    X_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv')
    Y_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv')

    proba = rf.predict_proba(X_test)[:,1]
    precision, recall, pr_thresholds = precision_recall_curve(Y_test, proba)

    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    rf_binary_threshold = pr_thresholds[np.argmax(f1_scores)]
    print(f'RF binary threshold: {rf_binary_threshold:.4f}')

    benign_proba = proba[Y_test.values.ravel() == 0]
    t1_rf = np.percentile(benign_proba, 90)
    t2_rf = np.percentile(benign_proba, 95)
    t3_rf = np.percentile(benign_proba, 99)
    print(f'RF tiers: {t1_rf:.4f}, {t2_rf:.4f}, {t3_rf:.4f}')

    thresholds = {'rf': [float(t1_rf), float(t2_rf), float(t3_rf)],
                  'rf_binary': float(rf_binary_threshold),
                  'ae': [float(ae_t1), float(ae_t2), float(ae_t3)],
                  'ae_binary': float(ae_binary_threshold),
                  'ae_max': float(ae_max_threshold)
                  }

    with open(BASE_DIR.parent /'models'/'artifacts'/'thresholds.json', 'w') as f:
        json.dump(thresholds, f)

if __name__ == "__main__":
    calibrate_thresholds()