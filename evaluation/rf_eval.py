import pandas as pd
import numpy as np
import util.paths as p

from sklearn.metrics import classification_report
from evaluation.helper import print_report, print_indented
from models.definitions.random_forest import construct_model, get_predictions
from util.feature_retrieval import get_rf_labels_testing, get_rf_features_testing, get_rf_categories_testing
from util.thresholds import get_thresholds
from util.logger import get_logger
LOGGER = get_logger(__name__)



# <---------- Validation functions ---------->
def source_type_valid(source_type) -> bool:
    if source_type not in ['cicids', 'unswnb']:
        LOGGER.error('Invalid source type')
        return False
    return True


def features_path_valid(features_path) -> bool:
    if features_path is not None and not features_path.exists():
        LOGGER.error('Invalid feature path')
        return False
    return True


def feature_set_valid(features) -> bool:
    if features is None:
        LOGGER.error('Imported feature set is invalid')
        return False
    return True



# <---------- Feature retrieval ---------->
def get_validation_feature_set(features_path, source_type) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    if features_path is None:
        validation_labels = get_rf_labels_testing()
        validation_features = get_rf_features_testing()
        return validation_features, validation_labels

    features_df = pd.read_csv(features_path, low_memory=False)
    validation_labels = pd.DataFrame()
    validation_features = pd.DataFrame()
    match source_type:
        case 'cicids':
            validation_labels = (features_df['Label'].str.strip().str.lower() != 'benign').astype(int)
            validation_features = features_df.drop('Label', axis=1)
        case 'unswnb':
            validation_labels = (features_df['Label'].astype(int))
            validation_features = features_df.drop(
                ['Unnamed: 0', 'Source IP', 'Destination IP', 'Source Port', 'Destination Port', 'Start time',
                 'Last time', 'Attack category', 'Label'], axis=1)
        case _:
            LOGGER.error('Source type is invalid')
            return None

    return validation_features, validation_labels


def get_test_train_feature_set(features_path, features):
    if features_path: # when there's already validation features, no need to get the cicids ones
        empty_df = pd.DataFrame()
        return empty_df, features

    # default to the cicids test-train features (deduplicated later)
    training_features = pd.read_csv(p.RF_TRAIN_PATH, low_memory=False)
    testing_features = pd.read_csv(p.RF_TEST_PATH, low_memory=False)
    return training_features, testing_features


def get_validation_categories(features_path, source_type, unique_mask):
    if features_path:
        validation_categories = pd.DataFrame()
        match source_type:
            case 'cicids':
                validation_categories = pd.read_csv(features_path, low_memory=False)['Label']
            case 'unswnb':
                validation_categories = pd.read_csv(features_path, low_memory=False)['Attack category']
            case _:
                LOGGER.error('Source type is invalid')
                return None
        return validation_categories, validation_categories[unique_mask.values]

    test_categories = get_rf_categories_testing()
    return test_categories, test_categories[unique_mask.values]



# <---------- Running individual reports & helper funcs ---------->
def deduplicate_datasets(train_df, test_df, y_test):
    train_hashes = set(train_df.round(2).apply(lambda r: hash(tuple(r)), axis=1))
    test_hashes = test_df.round(2).apply(lambda r: hash(tuple(r)), axis=1)
    unique_mask = ~test_hashes.isin(train_hashes)
    test_features_clean = test_df[unique_mask.values]
    test_labels_clean = y_test[unique_mask.values]

    return test_features_clean, test_labels_clean, unique_mask


def run_binary_report(clean_predictions, clean_labels, return_eval):
    errors = (clean_predictions != clean_labels.values.ravel()).sum()
    total = len(clean_labels)

    if return_eval: # return structured dict of results
        return {'Errors': int(errors), 'Total': total, 'Percentage Error': int(errors) / total,
                'False Positives': int(((clean_predictions == 1) & (clean_labels.values.ravel() == 0)).sum()),
                'False Negatives': int(((clean_predictions == 0) & (clean_labels.values.ravel() == 1)).sum())}

    # print all the results
    print("=== BINARY (deduplicated) ===")
    print(classification_report(clean_labels, clean_predictions))
    print(f"Total errors: {errors} out of {total} ({errors / total:.4%})")
    print(f"False positives: {((clean_predictions == 1) & (clean_labels.values.ravel() == 0)).sum()}")
    print(f"False negatives: {((clean_predictions == 0) & (clean_labels.values.ravel() == 1)).sum()}")
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
        attack_labels_mask = malicious_labels == attack
        recall = (malicious_proba[attack_labels_mask] > rf_binary_threshold).mean()
        avg_score = malicious_proba[attack_labels_mask].mean()
        num_attacks = attack_labels_mask.sum()
        recalls.append(recall)
        per_category_eval[attack] = {'Count': int(num_attacks), 'Recall': float(recall), 'Avg score': float(avg_score)}

    return per_category_eval, float(np.mean(recalls))


# ------- Main evaluation function -------
def evaluate_model(return_eval=False, validation_features_path=None, source_type='cicids'):
    if not p.processed_dataset_exists() or not p.thresholds_exist():
        return None
    if not source_type_valid(source_type) or not features_path_valid(validation_features_path):
        return None

    rf = construct_model()
    rf_binary_threshold = get_thresholds()['rf_binary']
    validation_feature_set = get_validation_feature_set(validation_features_path, source_type)

    if not feature_set_valid(validation_feature_set):
        return None

    validation_features, validation_labels = validation_feature_set
    proba, predictions = get_predictions(rf, rf_binary_threshold, validation_features)

    training_features, testing_features = get_test_train_feature_set(validation_features_path, validation_features)
    clean_validation_features, clean_validation_labels, unique_mask = deduplicate_datasets(training_features, testing_features, validation_labels)

    categories = get_validation_categories(validation_features_path, source_type, unique_mask)
    if categories is None:
        return None

    y_categories, categories_clean = categories
    proba_clean, clean_predictions = get_predictions(rf, rf_binary_threshold, clean_validation_features)

    per_category_evaluation_dict = {}
    binary_eval = run_binary_report(clean_predictions, clean_validation_labels, return_eval)
    category_eval = run_categorical_eval(rf_binary_threshold, clean_validation_labels, proba_clean, categories_clean, return_eval)

    # populate per-category evaluation
    per_category_eval, macro_recall = category_eval
    per_category_evaluation_dict['Binary'] = binary_eval
    per_category_evaluation_dict['Per-category Eval'] = per_category_eval
    per_category_evaluation_dict['Macro recall'] = macro_recall

    if not return_eval:
        print_report(validation_labels, predictions)
        print_indented(per_category_evaluation_dict)
        return None

    return clean_validation_labels, clean_predictions, per_category_evaluation_dict


if __name__ == '__main__':
    from pathlib import Path

    BASE_DIR = Path(__file__).parent

    results = evaluate_model(validation_features_path=BASE_DIR.parent / 'experiments' / 'csv\'s' / 'bq1' / 'rf_cicids.csv', return_eval=False)
    if results is not None:
        truth, prediction, categorical_eval = results
        print(classification_report(truth, prediction), categorical_eval)