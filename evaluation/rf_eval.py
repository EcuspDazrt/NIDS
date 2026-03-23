import pandas as pd
import numpy as np
import json
from sklearn.metrics import classification_report

from models.definitions.random_forest import construct_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

def evaluate_model():
    rf = construct_model()

    if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()

    with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
        t = json.load(f)
    rf_binary_threshold = t['rf_binary']

    if not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv').exists() or not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    X_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv')
    Y_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv')

    proba = rf.predict_proba(X_test)[:,1]
    Y_pred = (proba > rf_binary_threshold).astype(int)

    print(classification_report(Y_test, Y_pred))

    # cleaned up dataset without duplicate columns

    train_df = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_training.csv')
    test_df = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_testing.csv')

    # deduplicated, exact duplicates only
    train_hashes = set(train_df.round(2).apply(lambda r: hash(tuple(r)), axis=1))
    test_hashes = test_df.round(2).apply(lambda r: hash(tuple(r)), axis=1)
    unique_mask = ~test_hashes.isin(train_hashes)
    test_features_clean = test_df[unique_mask.values]
    test_labels_clean = Y_test[unique_mask.values]

    # also get category labels for clean set
    Y_categories = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'rf_categories_testing.csv')
    categories_clean = Y_categories[unique_mask.values]

    proba_clean = rf.predict_proba(test_features_clean)[:, 1]
    Y_pred_clean = (proba_clean > rf_binary_threshold).astype(int)

    # binary report
    print("=== BINARY (deduplicated) ===")
    print(classification_report(test_labels_clean, Y_pred_clean))
    errors = (Y_pred_clean != test_labels_clean.values.ravel()).sum()
    total = len(test_labels_clean)
    print(f"Total errors: {errors} out of {total} ({errors / total:.4%})")
    print(f"False positives: {((Y_pred_clean == 1) & (test_labels_clean.values.ravel() == 0)).sum()}")
    print(f"False negatives: {((Y_pred_clean == 0) & (test_labels_clean.values.ravel() == 1)).sum()}")

    # per-category report on malicious only
    print("=== PER CATEGORY (deduplicated) ===")
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
        print(f"{attack:40s} n={count:5d} recall={recall:.1%} avg_score={avg_score:.3f}")

    print(f"\nMacro recall across categories: {np.mean(recalls):.1%}")

if __name__ == '__main__':
    evaluate_model()