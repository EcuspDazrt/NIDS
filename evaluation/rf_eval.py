import pandas as pd
import numpy as np
import json
from sklearn.metrics import classification_report

from models.definitions.random_forest import construct_model

# pathing
from pathlib import Path
BASE_DIR = Path(__file__).parent

rf_categories_path = BASE_DIR.parent / 'datasets' / 'processed' / 'rf_categories_testing.csv'
rf_training_path = BASE_DIR.parent / 'datasets' / 'processed' / 'rf_training.csv'
rf_testing_path = BASE_DIR.parent / 'datasets' / 'processed' / 'rf_testing.csv'
rf_labels_path = BASE_DIR.parent / 'datasets' / 'processed' / 'rf_labels_testing.csv'

thresholds_path = BASE_DIR.parent / 'models' / 'artifacts' / 'thresholds.json'

# ------- Checks for dependencies and retrieves them if they do not exist -------
def check_dataset():
    if not rf_testing_path.exists() or not rf_labels_path.exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

def check_thresholds():
    if not thresholds_path.exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()


# ------- Retrieves information used in the evaluation -------
def get_threshold():
    with open(thresholds_path) as f:
        t = json.load(f)
    rf_binary_threshold = t['rf_binary']

    return rf_binary_threshold

def get_features(features_path, source_type):
    if features_path is None:
        y_test = pd.read_csv(rf_labels_path, low_memory=False)
        x_test = pd.read_csv(rf_testing_path, low_memory=False)

    else:
        df = pd.read_csv(features_path, low_memory=False)
        if source_type == 'cicids':
            y_test = (df['Label'].str.strip().str.lower() != 'benign').astype(int)
            x_test = df.drop('Label', axis=1)
        elif source_type == 'unswnb':
            y_test = (df['Label'].astype(int))
            x_test = df.drop(['Unnamed: 0', 'Source IP', 'Destination IP', 'Source Port', 'Destination Port', 'Start time', 'Last time', 'Attack category', 'Label'], axis=1)
        else:
            print('Invalid source type...')
            return None
    return x_test, y_test

def get_predictions(rf, rf_binary_threshold, x_test):
    proba = rf.predict_proba(x_test)[:,1]
    y_pred = (proba > rf_binary_threshold).astype(int)

    return proba, y_pred

def get_dataframes(features_path, x_test):
    if not features_path:
        train_df = pd.read_csv(rf_training_path, low_memory=False)
        test_df = pd.read_csv(rf_testing_path, low_memory=False)
    else:
        train_df = pd.DataFrame()
        test_df = x_test

    return train_df, test_df

def get_categories(features_path, source_type, unique_mask):
    if not features_path:
        y_categories = pd.read_csv(rf_categories_path)
    else:
        if source_type == 'cicids':
            y_categories = pd.read_csv(features_path, low_memory=False)['Label']
        elif source_type == 'unswnb':
            y_categories = pd.read_csv(features_path, low_memory=False)['Attack category']
        else:
            print('Invalid source type...')
            return None

    categories_clean = y_categories[unique_mask.values]

    return y_categories, categories_clean

def get_category_labels(rf, rf_binary_threshold, test_features_clean):
    proba_clean = rf.predict_proba(test_features_clean)[:, 1]
    y_pred_clean = (proba_clean > rf_binary_threshold).astype(int)

    return proba_clean, y_pred_clean



# ------- Carries out crucial functionality in the evaluation -------
def deduplicate_datasets(train_df, test_df, y_test):
    train_hashes = set(train_df.round(2).apply(lambda r: hash(tuple(r)), axis=1))
    test_hashes = test_df.round(2).apply(lambda r: hash(tuple(r)), axis=1)
    unique_mask = ~test_hashes.isin(train_hashes)
    test_features_clean = test_df[unique_mask.values]
    test_labels_clean = y_test[unique_mask.values]

    return test_features_clean, test_labels_clean, unique_mask

def run_binary_report(y_pred_clean, test_labels_clean, return_eval):
    errors = (y_pred_clean != test_labels_clean.values.ravel()).sum()
    total = len(test_labels_clean)

    if return_eval:
        # return structured dict of results
        return {'Errors': int(errors), 'Total': total, 'Percentage Error': int(errors) / total,
                'False Positives': int(((y_pred_clean == 1) & (test_labels_clean.values.ravel() == 0)).sum()),
                'False Negatives': int(((y_pred_clean == 0) & (test_labels_clean.values.ravel() == 1)).sum())}

    # print all the results
    print("=== BINARY (deduplicated) ===")
    print(classification_report(test_labels_clean, y_pred_clean))
    print(f"Total errors: {errors} out of {total} ({errors / total:.4%})")
    print(f"False positives: {((y_pred_clean == 1) & (test_labels_clean.values.ravel() == 0)).sum()}")
    print(f"False negatives: {((y_pred_clean == 0) & (test_labels_clean.values.ravel() == 1)).sum()}")
    return None

def run_categorical_eval(rf_binary_threshold, test_labels_clean, proba_clean, categories_clean, return_eval):
    if not return_eval:
        print("=== PER CATEGORY (deduplicated) ===")

    malicious_mask = test_labels_clean.values.ravel() == 1
    malicious_proba = proba_clean[malicious_mask]
    malicious_labels = categories_clean.values.ravel()[malicious_mask]

    recalls = []

    per_category_eval = {}
    for attack in sorted(set(malicious_labels)):
        mask = malicious_labels == attack
        recall = (malicious_proba[mask] > rf_binary_threshold).mean()
        avg_score = malicious_proba[mask].mean()
        count = mask.sum()
        recalls.append(recall)
        if return_eval:
            per_category_eval[attack] = {'Count': int(count), 'Recall': float(recall), 'Avg score': float(avg_score)}
            continue

        print(f"{attack:40s} n={count:5d} recall={recall:.1%} avg_score={avg_score:.3f}")

    if return_eval:
        return per_category_eval, float(np.mean(recalls))

    print(f"Macro recall across categories: {np.mean(recalls):.1%}")
    return None


# ------- Main evaluation function -------
def evaluate_model(return_eval=False, features_path=None, source_type='cicids'):
    rf = construct_model()
    check_thresholds()
    check_dataset()
    rf_binary_threshold = get_threshold()

    if source_type not in ['cicids', 'unswnb']:
        print('Invalid source type...')
        return None
    if features_path is not None and not features_path.exists():
        print('Invalid feature path...')
        return None
    features = get_features(features_path, source_type)
    if features is None:
        return None

    x_test, y_test = features
    proba, y_pred = get_predictions(rf, rf_binary_threshold, x_test)

    train_df, test_df = get_dataframes(features_path, x_test)
    test_features_clean, test_labels_clean, unique_mask = deduplicate_datasets(train_df, test_df, y_test)

    categories = get_categories(features_path, source_type, unique_mask)
    if categories is None:
        return None

    y_categories, categories_clean = categories
    proba_clean, y_pred_clean = get_category_labels(rf, rf_binary_threshold, test_features_clean)


    categorical_eval = {}
    binary_eval = run_binary_report(y_pred_clean, test_labels_clean, return_eval)
    category_eval = run_categorical_eval(rf_binary_threshold, test_labels_clean, proba_clean, categories_clean, return_eval)

    # populate categorical_eval
    if return_eval:
        per_category_eval, macro_recall = category_eval

        categorical_eval['Binary'] = binary_eval
        categorical_eval['Per-category Eval'] = per_category_eval
        categorical_eval['Macro recall'] = macro_recall

    if return_eval:
        return test_labels_clean, y_pred_clean, categorical_eval

    print(classification_report(y_test, y_pred))
    return None

if __name__ == '__main__':
    results = evaluate_model(features_path=BASE_DIR.parent / 'experiments' / 'csv\'s' / 'bq1' / 'rf_cicids.csv', return_eval=False)
    if results is not None:
        truth, prediction, categorical_eval = results
        print(classification_report(truth, prediction), categorical_eval)