import torch
import json
import pandas as pd
from sklearn.metrics import classification_report

from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model
from inference.inference import categorize_risk

from pathlib import Path
BASE_DIR = Path(__file__).parent

def evaluate_model():
    model = construct_model(load=True)

    if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()

    with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
        t = json.load(f)
    thresholds = t['ae']
    binary_threshold = t['ae_binary']

    if not Path(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_benign.csv').exists() or not Path(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_malicious.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    features_benign = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_benign.csv', low_memory=False)
    features_malicious = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_malicious.csv', low_memory=False)
    features = pd.concat([features_benign, features_malicious], ignore_index=True)
    x = create_dataset(features, loader=False)

    with torch.no_grad():
        recon = model(x)
        error = ((x - recon) ** 2).mean(dim=1)

    y_true = pd.Series([0] * len(features_benign) + [1] * len(features_malicious))
    binary_predictions = (error > binary_threshold).int()
    print(classification_report(y_true, binary_predictions))

    categories = categorize_risk(error, thresholds)
    for i, label in enumerate(['normal', 'elevated', 'suspicious', 'severe']):
        mask = categories == i
        if mask.sum() > 0:
            actual_attack_rate = y_true[mask].mean()
            print(f'{label}: {mask.sum()} flows, {actual_attack_rate:.1%} actually malicious')

if __name__ == '__main__':
    evaluate_model()