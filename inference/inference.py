import json

import pandas as pd
import numpy as np
import joblib as jb
import torch

from models.definitions.autoencoder import construct_model as construct_ae
from models.definitions.random_forest import construct_model as construct_rf
from scripts.build_dataset import create_dataset

from pathlib import Path
BASE_DIR = Path(__file__).parent

def categorize_risk(scores, thresholds):
    t1, t2, t3 = thresholds
    scores = scores.detach().numpy() if torch.is_tensor(scores) else np.array(scores)  # ensure it's a NumPy array
    categories = np.zeros_like(scores, dtype=int)

    categories[(scores > t1) & (scores <= t2)] = 1
    categories[(scores > t2) & (scores <= t3)] = 2
    categories[scores > t3] = 3

    return categories

def calculate_percent(categories, scores, thresholds, max_threshold):
    t1, t2, t3 = thresholds
    scores = scores.detach().numpy() if torch.is_tensor(scores) else np.array(scores)
    min_max_thresholds = np.array([0, t1, t2, t3, max_threshold])

    percentages = ((np.minimum(scores, min_max_thresholds[4]) - min_max_thresholds[categories]) /
                   (min_max_thresholds[categories+1] - min_max_thresholds[categories] + 1e-8) * 25) + 25 * categories

    return percentages

def infer(ae, rf, ae_features, rf_features, ae_thresholds, max_ae_threshold, rf_thresholds, scaler):
    ae_features = pd.DataFrame([ae_features])
    rf_features = pd.DataFrame([rf_features])

    ae_features = create_dataset(ae_features, loader=False)
    rf_features = scaler.transform(rf_features)

    with torch.no_grad():
        ae_recon = ae(ae_features)
        ae_score = ((ae_features - ae_recon) ** 2).mean(dim=1)
    rf_score = rf.predict_proba(rf_features)[:, 1]

    ae_category = categorize_risk(ae_score, ae_thresholds)
    rf_category = categorize_risk(rf_score, rf_thresholds)

    ae_percent = calculate_percent(ae_category, ae_score, ae_thresholds, max_ae_threshold)

    return int(ae_percent[0]), int(ae_category[0]), int(rf_category[0]), float(ae_score[0].item()), float(rf_score[0].item())

def inference_process(flow_queue, results_queue, models_ready=None):
    from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
    from alerts.logger import init_db, log_flow

    init_db()

    ae = construct_ae(load=True)
    ae.eval()
    rf = construct_rf()

    if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()

    with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
        t = json.load(f)

    ae_thresholds = t['ae']
    max_ae_threshold = t['ae_max']
    rf_thresholds = t['rf']

    rf_scaler = jb.load(BASE_DIR.parent / 'models' / 'artifacts' / 'rf_scaler.pkl')

    if models_ready:
        models_ready.set()

    while True:
        flow = flow_queue.get()
        ae_features = extract_ae(flow)
        rf_features = extract_rf(flow)
        ae_percent, ae_category, rf_category, ae_score, rf_score = infer(ae, rf, ae_features, rf_features, ae_thresholds, max_ae_threshold, rf_thresholds, rf_scaler)

        log_flow(flow, ae_percent, ae_category, rf_category, ae_score, rf_score)
        results_queue.put([ae_percent, ae_category, rf_category])
