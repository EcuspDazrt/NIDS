import pandas as pd
import numpy as np
import util.paths as p
import torch

from datetime import datetime, timezone
from util.thresholds import get_thresholds
from models.definitions.autoencoder import construct_model as construct_ae
from models.definitions.random_forest import construct_model as construct_rf
from scripts.build_dataset import create_dataset

def load_ja3_blocklist():
    if not p.BLOCKLIST_PATH.exists():
        return set()
    with open(p.BLOCKLIST_PATH) as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith('#'))

MALICIOUS_JA3 = load_ja3_blocklist()

def ja3_is_malicious(ja3_hash):
    if ja3_hash is None:
        return False
    return ja3_hash in MALICIOUS_JA3

def categorize_risk(scores, thresholds):
    if len(thresholds) == 4:
        t1, t2, t3, _ = thresholds
    else:
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

def infer(ae, rf, ae_features, rf_features, ae_thresholds, max_ae_threshold, rf_thresholds, ja3_hash=None):
    ae_features = pd.DataFrame([ae_features])
    rf_features = pd.DataFrame([rf_features])

    ae_features = create_dataset(ae_features, loader=False)

    with torch.no_grad():
        ae_recon = ae(ae_features)
        ae_score = ((ae_features - ae_recon) ** 2).mean(dim=1)
    rf_score = rf.predict_proba(rf_features)[:, 1]

    ae_category = categorize_risk(ae_score, ae_thresholds)
    rf_category = categorize_risk(rf_score, rf_thresholds)

    ae_percent = calculate_percent(ae_category, ae_score, ae_thresholds, max_ae_threshold)

    ja3_malicious = ja3_is_malicious(ja3_hash)

    return int(ae_percent[0]), int(ae_category[0]), int(rf_category[0]), float(ae_score[0].item()), float(rf_score[0].item()), ja3_malicious

def inference_process(flow_queue, results_queue, models_ready=None, alert_engine=None):
    from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
    from alerts.logger import init_db, log_flow
    init_db()

    if not p.artifacts_exist():
        raise Exception('[CRITICAL] Artifacts do not exist or were unable to be created.')
    models_ready.set()

    ae = construct_ae(load=True)
    ae.eval()
    rf = construct_rf()
    rf.n_jobs = 1

    thresholds = get_thresholds()
    ae_thresholds = thresholds['ae'][:3]
    max_ae_threshold = thresholds['ae'][3]
    rf_thresholds = thresholds['rf']

    while True:
        flow = flow_queue.get()
        ae_features = extract_ae(flow)
        rf_features = extract_rf(flow)
        ja3_hash = flow['ja3_hash']

        ae_percent, ae_category, rf_category, ae_score, rf_score, ja3_malicious = infer(ae, rf, ae_features, rf_features, ae_thresholds, max_ae_threshold, rf_thresholds, ja3_hash=ja3_hash)

        alert_engine.evaluate(ae_category, rf_category, rf_score, ja3_hash, ja3_malicious, flow)
        log_flow(flow, ae_percent, ae_category, rf_category, ae_score, rf_score, ae_features, rf_features, ja3_hash, ja3_malicious)
        results_queue.put({'type':'flow','payload':[ae_percent, ae_category, 3 if ja3_malicious else rf_category, datetime.now(timezone.utc).isoformat()]})