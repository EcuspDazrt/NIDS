import pandas as pd
import numpy as np
import json
from sklearn.metrics import classification_report

from models.definitions.random_forest import construct_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

def evaluate_model(return_eval=False, features_path=None, source_type='cicids'):
    rf = construct_model()
    categorical_eval = ''

    if source_type not in ['cicids', 'unswnb']:
        print('Invalid source type...')
        return None
    if features_path is not None and not features_path.exists():
        print('Invalid feature path...')
        return None
    if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()

    with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
        t = json.load(f)
    rf_binary_threshold = t['rf_binary']

    if not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv').exists() or not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    if features_path is None:
        Y_test = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_labels_testing.csv', low_memory=False)
        X_test = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_testing.csv', low_memory=False)
    else:
        df = pd.read_csv(features_path, low_memory=False)
        if source_type == 'cicids':
            Y_test = (df['Label'].str.strip().str.lower() != 'benign').astype(int)
        elif source_type == 'unswnb':
            Y_test = (df['Label'].astype(int))
        else:
            print('Invalid source type...')
            return None
        X_test = df.drop('Label', axis=1)

    proba = rf.predict_proba(X_test)[:,1]
    Y_pred = (proba > rf_binary_threshold).astype(int)

    if not return_eval:
        print(classification_report(Y_test, Y_pred))

    # import both the training and testing rf sets
    if not features_path:
        train_df = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_training.csv', low_memory=False)
        test_df = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_testing.csv', low_memory=False)
    else:
        train_df = pd.DataFrame()
        test_df = X_test


    # de-duplicate the datasets
    train_hashes = set(train_df.round(2).apply(lambda r: hash(tuple(r)), axis=1))
    test_hashes = test_df.round(2).apply(lambda r: hash(tuple(r)), axis=1)
    unique_mask = ~test_hashes.isin(train_hashes)
    test_features_clean = test_df[unique_mask.values]
    test_labels_clean = Y_test[unique_mask.values]

    # also get category labels for clean set
    if not features_path:
        Y_categories = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_categories_testing.csv')
    else:
        if source_type == 'cicids':
            Y_categories = pd.read_csv(features_path, low_memory=False)['Label']
        elif source_type == 'unswnb':
            Y_categories = pd.read_csv(features_path, low_memory=False)['Attack category']
        else:
            print('Invalid source type...')
            return None

    categories_clean = Y_categories[unique_mask.values]

    proba_clean = rf.predict_proba(test_features_clean)[:, 1]
    Y_pred_clean = (proba_clean > rf_binary_threshold).astype(int)

    # binary report
    errors = (Y_pred_clean != test_labels_clean.values.ravel()).sum()
    total = len(test_labels_clean)
    if not return_eval:
        print("=== BINARY (deduplicated) ===")
        print(classification_report(test_labels_clean, Y_pred_clean))
    categorical_eval += f"Total errors: {errors} out of {total} ({errors / total:.4%})\n"
    categorical_eval += f"False positives: {((Y_pred_clean == 1) & (test_labels_clean.values.ravel() == 0)).sum()}\n"
    categorical_eval += f"False negatives: {((Y_pred_clean == 0) & (test_labels_clean.values.ravel() == 1)).sum()}\n"

    # per-category report on malicious only
    categorical_eval += "=== PER CATEGORY (deduplicated) ===\n"
    malicious_mask = test_labels_clean.values.ravel() == 1
    malicious_proba = proba_clean[malicious_mask]
    malicious_labels = categories_clean.values.ravel()[malicious_mask]

    recalls = []
    for attack in sorted(set(malicious_labels)):
        mask = malicious_labels == attack
        recall = (malicious_proba[mask] > rf_binary_threshold).mean()
        avg_score = malicious_proba[mask].mean()
        count = mask.sum()
        recalls.append(recall)
        categorical_eval += f"{attack:40s} n={count:5d} recall={recall:.1%} avg_score={avg_score:.3f}\n"

    categorical_eval += f"\nMacro recall across categories: {np.mean(recalls):.1%}"

    if not return_eval:
        print(categorical_eval)
        return None

    return test_labels_clean, Y_pred_clean, categorical_eval

if __name__ == '__main__':
    results = evaluate_model(features_path=BASE_DIR.parent / 'experiments' / 'csv\'s' / 'bq1' / 'rf_cicids.csv', return_eval=True)
    truth, prediction, categorical_eval = results
    print(classification_report(truth, prediction), categorical_eval)