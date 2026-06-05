import torch
import pandas as pd
import util.paths as p

from sklearn.metrics import classification_report
from evaluation.helper import print_report, print_indented
from util.thresholds import get_thresholds
from util.feature_retrieval import get_ae_testing
from scripts.build_dataset import create_dataset
from retraining.retrain_ae import recalibrate_ae_thresholds
from models.definitions.autoencoder import construct_model, get_error
from inference.inference import categorize_risk

from util.logger import get_logger
LOGGER = get_logger(__name__)


def get_features(features_benign_path, features_malicious_path):
    if features_benign_path is None or features_malicious_path is None:
        features = get_ae_testing()
        features_benign = features['ae_testing_benign']
        features_malicious = features['ae_testing_malicious']
    else:
        features_benign = pd.read_csv(features_benign_path, low_memory=False)
        features_malicious = pd.read_csv(features_malicious_path, low_memory=False)

    return features_benign, features_malicious


def get_classification(error, binary_threshold, features_benign, features_malicious):
    labels = pd.Series([0] * len(features_benign) + [1] * len(features_malicious))
    binary_predictions = (error > binary_threshold).astype(int)

    return labels, binary_predictions


def get_categorical_eval(categories, return_eval, y_true):
    categorical_eval = {}
    for i, label in enumerate(['Normal', 'Elevated', 'Suspicious', 'Severe']):
        mask = categories == i
        if mask.sum() > 0:
            actual_attack_rate = y_true[mask].mean()
            categorical_eval[label] = {'Flow Count': int(mask.sum()), 'Malicious Rate': float(actual_attack_rate)}
            if not return_eval:
                LOGGER.info(f'{label}: {mask.sum()} flows, {actual_attack_rate:.1%} actually malicious')

    return categorical_eval if return_eval else None


def get_construction_layers(construction):
    construction_layers = [int(x) for x in construction.split('_')] if construction else [20, 32, 16, 8]
    l1, l2, l3 = construction_layers[1:]
    return l1, l2, l3


# ------- Runs the main evaluation logic -------
def run_eval(ae=None, features_benign_path=None, features_malicious_path=None, return_eval=False):
    # returns the binary labels and predictions as well as a dictionary that has the results of evaluation-by-category
    if not ae:
        return None
    ae.eval()

    thresholds = get_thresholds()
    ae_thresholds = thresholds['ae']
    ae_binary_threshold = thresholds['ae_binary']

    # get features
    features_benign, features_malicious = get_features(features_benign_path, features_malicious_path)
    all_features = create_dataset(pd.concat([features_benign, features_malicious], ignore_index=True), loader=False)

    # get model predictions
    error = get_error(ae, all_features)
    labels, predictions = get_classification(error, ae_binary_threshold, features_benign, features_malicious)

    categories = categorize_risk(error, ae_thresholds)
    categorical_eval = get_categorical_eval(categories, return_eval, labels)

    if return_eval:
        return labels, predictions, categorical_eval

    LOGGER.info(classification_report(labels, predictions))
    return None


def run_manual_evaluation(construction, features_benign_path, features_malicious_path):
    model_paths = sorted((p.ARTIFACTS_DIR / 'manual_backups' / f'{construction}_construction').glob('ae_model_*'))
    l1, l2, l3 = get_construction_layers(construction)

    for path in model_paths:
        LOGGER.info(f'Evaluating {path.stem.replace('ae_model_', '').replace('_', ' ')}\n')
        model = construct_model(l1=l1, l2=l2, l3=l3)
        model.load_state_dict(torch.load(path))
        recalibrate_ae_thresholds(model)
        run_eval(model, features_benign_path=features_benign_path, features_malicious_path=features_malicious_path)

def evaluate_model(manual_eval=False, return_eval=False, construction='', features_benign_path=None, features_malicious_path=None):
    if not p.processed_dataset_exists() or not p.thresholds_exist():
        return None

    l1, l2, l3 = get_construction_layers(construction)

    if manual_eval:
        run_manual_evaluation(construction, features_benign_path, features_malicious_path)
    else:
        model = construct_model(load=True, l1=l1, l2=l2, l3=l3)
        eval_results = run_eval(model, features_benign_path, features_malicious_path, return_eval=return_eval)
        if return_eval:
            return eval_results

    return None

if __name__ == '__main__':
    eval = evaluate_model(
        manual_eval=False,
        return_eval=True,
    )
    if eval is not None:
        labels, binary_predictions, categorical_eval = eval
        print_report(labels, binary_predictions)
        print_indented(categorical_eval)
