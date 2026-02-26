import pandas as pd
from pathlib import Path
import numpy as np
import torch
import random

from models.definitions.autoencoder import construct_model as construct_ae
from models.definitions.random_forest import construct_model as construct_rf

from features.extract import extract_features_ae as extract_ae, extract_features_rf as extract_rf
from scripts.build_dataset import create_dataset

ae = construct_ae()
ae.eval()
rf = construct_rf()

def find_ae_thresholds():
    from evaluation.ae_eval import evaluate_model as evaluate
    error = evaluate(show_error_flag=False)

    t1 = np.percentile(error.detach().numpy(), 92)
    t2 = np.percentile(error.detach().numpy(), 95)
    t3 = np.percentile(error.detach().numpy(), 99)
    t4 = np.percentile(error.detach().numpy(), 99.9)

    return [t1, t2, t3], t4

AE_LABELS = ['normal', 'elevated', 'suspicious', 'severe']
AE_THRESHOLDS, MAX_AE_THRESHOLD = find_ae_thresholds()
RF_LABELS = ['safe', 'potential', 'likely', 'danger']
RF_THRESHOLDS = [0.05, 0.1, 0.125]

BASE_DIR = Path(__file__).resolve().parents[1]
X_test = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_rf_testing.csv')
print('finished reading csv files...')

def categorize_risk(scores, thresholds):
    t1, t2, t3 = thresholds
    scores = scores.detach().numpy() if torch.is_tensor(scores) else np.array(scores)  # ensure it's a NumPy array
    categories = np.zeros_like(scores, dtype=int)

    categories[(scores > t1) & (scores <= t2)] = 1
    categories[(scores > t2) & (scores <= t3)] = 2
    categories[scores > t3] = 3

    return categories

def return_risk_labels(scores, thresholds, labels):
    cats = categorize_risk(scores, thresholds)
    return [labels[c] for c in cats]

def calculate_percent(categories, scores, thresholds):
    t1, t2, t3 = thresholds
    scores = scores.detach().numpy() if torch.is_tensor(scores) else np.array(scores)
    min_max_thresholds = np.array([0, t1, t2, t3, MAX_AE_THRESHOLD])

    percentages = ((min(scores, min_max_thresholds[4]) - min_max_thresholds[categories]) /
                   (min_max_thresholds[categories+1] - min_max_thresholds[categories] + 1e-8) * 25) + 25 * categories

    return percentages

def infer():
    sample = X_test.sample(n=1)

    ae_features = extract_ae(sample)
    ae_features = create_dataset(ae_features, loader=False)
    rf_features = extract_rf(sample)

    ae_recon = ae(ae_features)
    ae_score = ((ae_features - ae_recon) ** 2).mean(dim=1)
    rf_score = rf.predict_proba(rf_features)[:, 1]

    ae_category = categorize_risk(ae_score, AE_THRESHOLDS)
    rf_category = categorize_risk(rf_score, RF_THRESHOLDS)

    ae_percent = calculate_percent(ae_category, ae_score, AE_THRESHOLDS)
    # print(f'percentages: {ae_percent}')

    # testing, not needed for system
    ae_guesses = return_risk_labels(ae_score, AE_THRESHOLDS, AE_LABELS)
    rf_guesses = return_risk_labels(rf_score, RF_THRESHOLDS, RF_LABELS)

    print(sample['Label'])
    print(ae_guesses, rf_guesses)

    return int(ae_percent[0]), int(ae_category[0]), int(rf_category[0])