import pandas as pd
import numpy as np
import torch

from pathlib import Path

from models.definitions.autoencoder import construct_model as construct_ae
from models.definitions.random_forest import construct_model as construct_rf
from scripts.build_dataset import create_dataset

ae = construct_ae()
ae.eval()
rf = construct_rf()

AE_FEATURE_ORDER = [
    "Duration", "In/Out Ratio", "Absolute Difference", "Byte Rate Asymmetry",
    "Forward Packet Rate", "Forward Byte Rate", "Forward Byte Mean", "Forward Byte Std",
    "Backward Packet Rate", "Backward Byte Rate", "Backward Byte Mean", "Backward Byte Std",
    "Forward IAT Mean", "Forward IAT Std", "Backward IAT Mean", "Backward IAT Std",
    "Active Mean", "Active Std", "Idle Mean", "Idle Std"
]

RF_FEATURE_ORDER = [
    'proto_0', 'proto_6', 'proto_17', 'Port', 'IP', 'Duration', 'In/Out Ratio',
    'Total Packets', 'Total Bytes', 'Total Packet Rate', 'Total Byte Rate', 'Total Byte Max', 'Total Byte Min', 'Total Byte Mean', 'Total Byte Std', 'Total Byte Variance',
    'Forward Packets', 'Forward Bytes', 'Forward Packet Rate', 'Forward Byte Rate', 'Forward Byte Max', 'Forward Byte Min', 'Forward Byte Mean', 'Forward Byte Std', 'Forward Byte Variance',
    'Backward Packets', 'Backward Bytes', 'Backward Packet Rate', 'Backward Byte Rate', 'Backward Byte Max', 'Backward Byte Min', 'Backward Byte Mean', 'Backward Byte Std', 'Backward Byte Variance',
    'Total IAT', 'Total IAT Max', 'Total IAT Min', 'Total IAT Mean', 'Total IAT Std', 'Total IAT Variance',
    'Forward IAT', 'Forward IAT Max', 'Forward IAT Min', 'Forward IAT Mean', 'Forward IAT Std', 'Forward IAT Variance',
    'Backward IAT', 'Backward IAT Max', 'Backward IAT Min', 'Backward IAT Mean', 'Backward IAT Std', 'Backward IAT Variance',
    'Active Max', 'Active Min', 'Active Mean', 'Active Std', 'Active Variance',
    'Idle Max', 'Idle Min', 'Idle Mean', 'Idle Std', 'Idle Variance',
    'Syn Ratio', 'Ack Ratio', 'Fin Ratio', 'Rst Ratio',
    'Syn Rate', 'Ack Rate', 'Fin Rate', 'Rst Rate',
    'Syn/Ack Ratio', 'Fin/Ack Ratio', 'Rst/Syn Ratio'
]

def find_ae_thresholds():
    from evaluation.ae_eval import evaluate_model as evaluate
    error = evaluate(show_error_flag=False)

    t1 = np.percentile(error.detach().numpy(), 92)
    t2 = np.percentile(error.detach().numpy(), 95)
    t3 = np.percentile(error.detach().numpy(), 99)
    t4 = np.percentile(error.detach().numpy(), 99.9)

    print(t1, t2, t3, t4)
    return [t1, t2, t3], t4

AE_LABELS = ['normal', 'elevated', 'suspicious', 'severe']
AE_THRESHOLDS, MAX_AE_THRESHOLD = find_ae_thresholds()
RF_LABELS = ['safe', 'potential', 'likely', 'danger']
RF_THRESHOLDS = [0.05, 0.1, 0.125]

# BASE_DIR =  Path(__file__).parent
# X_test = pd.read_csv(BASE_DIR.parent / 'datasets'/ 'raw'/ 'CICIDS2017'/ 'Aggregated'/ 'CICIDS2017_rf_testing.csv')
# print('finished reading csv files...')

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

def infer(ae_features, rf_features):
    ae_features = create_dataset(ae_features, loader=False)

    ae_recon = ae(ae_features)
    ae_score = ((ae_features - ae_recon) ** 2).mean(dim=1)
    rf_score = rf.predict_proba(rf_features)[:, 1]

    ae_category = categorize_risk(ae_score, AE_THRESHOLDS)
    rf_category = categorize_risk(rf_score, RF_THRESHOLDS)

    ae_percent = calculate_percent(ae_category, ae_score, AE_THRESHOLDS)

    # testing, not needed for system
    ae_guesses = return_risk_labels(ae_score, AE_THRESHOLDS, AE_LABELS)
    rf_guesses = return_risk_labels(rf_score, RF_THRESHOLDS, RF_LABELS)

    print(ae_guesses, rf_guesses)

    return int(ae_percent[0]), int(ae_category[0]), int(rf_category[0])

# def inference_testing():
#     from features.extract_training import extract_features_ae as extract_ae, extract_features_rf as extract_rf
#     sample = X_test.sample(n=1)
#     label = sample['Label']
#     print(label)
#
#     ae_features = extract_ae(sample)
#     rf_features = extract_rf(sample)
#
#     ae_percent, ae_score, rf_score = infer(ae_features, rf_features)
#
#     return ae_percent, ae_score, rf_score

def inference_process(flow_queue, results_queue):
    from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
    while True:
        flow = flow_queue.get()

        ae_features_dict = extract_ae(flow)
        ae_features_arr = np.array([ae_features_dict[key] for key in AE_FEATURE_ORDER])

        rf_features_dict = extract_rf(flow)
        rf_features_arr = np.array([rf_features_dict[key] for key in RF_FEATURE_ORDER])

        ae_percent, ae_score, rf_score = infer(ae_features_arr, rf_features_arr)

        results_queue.put([ae_percent, ae_score, rf_score])
