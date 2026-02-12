import pandas as pd
from pathlib import Path
import numpy as np
import torch

from models.autoencoder import construct_model as construct_ae
from models.random_forest import construct_model as construct_rf

from features.extract import extract_features_ae as extract_ae, extract_features_rf as extract_rf
from utils.build_dataset import create_dataset

ae = construct_ae()
ae.eval()
rf = construct_rf()

AE_LABELS = ['normal', 'elevated', 'suspicious', 'severe']
AE_THRESHOLDS = [0.10067157, 0.13295603, 0.2985995]
RF_LABELS = ['safe', 'potential', 'likely', 'danger']
RF_THRESHOLDS = [0.05, 0.1, 0.125]

BASE_DIR = Path(__file__).resolve().parents[1]
X_test = pd.read_csv(f'{BASE_DIR}/datasets/raw/CICIDS2017/Aggregated/CICIDS2017_rf_testing.csv')
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

def infer():
    for _ in range(1000):
        row = X_test.sample(n=1)
        ae_sample = extract_ae(row)
        ae_sample = create_dataset(ae_sample, loader=False)
        recon = ae(ae_sample)
        error = ((ae_sample - recon) ** 2).mean(dim=1)
        ae_guesses = return_risk_labels(error, AE_THRESHOLDS, AE_LABELS)
        print(row['Label'])

        rf_sample = extract_rf(row)
        rf_score = rf.predict_proba(rf_sample)[:, 1]
        rf_guesses = return_risk_labels(rf_score, RF_THRESHOLDS, RF_LABELS)
        print(ae_guesses, rf_guesses)
        input()

def find_thresholds():
    from autoencoder_eval import evaluate_model as eval
    import numpy as np
    error = eval(show_error_flag=False)

    t1 = np.percentile(error.detach().numpy(), 92)
    t2 = np.percentile(error.detach().numpy(), 95)
    t3 = np.percentile(error.detach().numpy(), 99)

    print(t1, t2, t3)
    return [t1, t2, t3]

a = find_thresholds()
infer()