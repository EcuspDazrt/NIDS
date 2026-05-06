import torch
import json
import pandas as pd
from sklearn.metrics import classification_report

from scripts.build_dataset import create_dataset
from scripts.retrain_ae import recalibrate_ae_thresholds
from models.definitions.autoencoder import construct_model
from inference.inference import categorize_risk

from pathlib import Path
BASE_DIR = Path(__file__).parent

benign_testing_path = BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv'
malicious_testing_path = BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_malicious.csv'

thresholds_path = BASE_DIR.parent / 'models' / 'artifacts' / 'thresholds.json'
artifacts_path =  BASE_DIR.parent / 'models' / 'artifacts'

# ------- Checks for dependencies and retrieves them if they do not exist -------
def check_dataset():
    if not benign_testing_path.exists() or not malicious_testing_path.exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

def check_thresholds():
    if not thresholds_path.exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()


# ------- Retrieves information used in the evaluation -------
def get_thresholds():
    with open(thresholds_path) as f:
        t = json.load(f)
    thresholds = t['ae']
    binary_threshold = t['ae_binary']

    return thresholds, binary_threshold

def get_features(features_benign_path, features_malicious_path):
    if features_benign_path is None or features_malicious_path is None:
        features_benign = pd.read_csv(benign_testing_path, low_memory=False)
        features_malicious = pd.read_csv(malicious_testing_path, low_memory=False)
    else:
        features_benign = pd.read_csv(features_benign_path, low_memory=False)
        features_malicious = pd.read_csv(features_malicious_path, low_memory=False)

    return features_benign, features_malicious

def get_error(ae=None, x=None):
    with torch.no_grad():
        recon = ae(x)
        error = ((x - recon) ** 2).mean(dim=1).numpy()

    return error

def get_classification(error, binary_threshold, features_benign, features_malicious):
    y_true = pd.Series([0] * len(features_benign) + [1] * len(features_malicious))
    binary_predictions = (error > binary_threshold).int()

    return y_true, binary_predictions

def get_categorical_eval(categories, return_eval, y_true):
    categorical_eval = {}
    for i, label in enumerate(['Normal', 'Elevated', 'Suspicious', 'Severe']):
        mask = categories == i
        if mask.sum() > 0:
            actual_attack_rate = y_true[mask].mean()
            categorical_eval[label] = {'Flow Count': int(mask.sum()), 'Malicious Rate': float(actual_attack_rate)}
            if not return_eval:
                print(f'{label}: {mask.sum()} flows, {actual_attack_rate:.1%} actually malicious')

    return categorical_eval if return_eval else None


# ------- Runs the main evaluation logic -------
def run_eval(ae=None, features_benign_path=None, features_malicious_path=None, return_eval=False):
    if not ae:
        return None

    ae.eval()
    thresholds, binary_threshold = get_thresholds()

    features_benign, features_malicious = get_features(features_benign_path, features_malicious_path)
    features = pd.concat([features_benign, features_malicious], ignore_index=True)

    x = create_dataset(features, loader=False)

    error = get_error(ae, x)
    y_true, binary_predictions = get_classification(error, binary_threshold, features_benign, features_malicious)

    categories = categorize_risk(error, thresholds)
    categorical_eval = get_categorical_eval(categories, return_eval, y_true)

    if return_eval:
        return y_true, binary_predictions, categorical_eval

    print(classification_report(y_true, binary_predictions))
    return None

def evaluate_model(manual_eval=False, return_eval=False, construction='', features_benign_path=None, features_malicious_path=None):
    check_dataset()

    construction_layers = [int(x) for x in construction.split('_')] if construction else [20, 32, 16, 8]
    l1, l2, l3 = construction_layers[1:]

    if manual_eval:

        model_paths = sorted((artifacts_path/'manual_backups'/f'{construction}_construction').glob('ae_model_*'))

        for path in model_paths:
            print(f'Evaluating {path.stem.replace('ae_model_', '').replace('_', ' ')}\n')
            model = construct_model(l1=l1, l2=l2, l3=l3)
            model.load_state_dict(torch.load(path))
            recalibrate_ae_thresholds(model)
            run_eval(model, features_benign_path=features_benign_path, features_malicious_path=features_malicious_path)

    else:
        model = construct_model(load=True, l1=l1, l2=l2, l3=l3)
        check_thresholds()
        eval_results = run_eval(model, features_benign_path, features_malicious_path, return_eval=return_eval)

        if return_eval:
            return eval_results

    return None

if __name__ == '__main__':
    eval = evaluate_model(
        manual_eval=False,
        return_eval=True,
        features_benign_path=r"C:\Users\London\Documents\GitHub\NIDS\experiments\csv's\final_ae_features.csv",
        features_malicious_path=r"C:\Users\London\Documents\GitHub\NIDS\experiments\csv's\final_ae_features.csv",
    )
    if eval is not None:
        y_pred, binary_predictions, categorical_eval = eval
        print(classification_report(y_pred, binary_predictions, output_dict=True))
        print(categorical_eval)