import util.paths as p
import pandas as pd

from scripts.build_dataset import create_dataset

# <---------- Singular file read ---------->
def get_ae_features_benign_testing(dataset=False) -> pd.DataFrame:
    ae_testing_benign = pd.read_csv(p.AE_TEST_BENIGN_PATH, low_memory=False)
    if dataset:
        return create_dataset(ae_testing_benign, loader=False)
    return ae_testing_benign

def get_ae_features_malicious_testing(dataset=False) -> pd.DataFrame:
    ae_testing_malicious = pd.read_csv(p.AE_TEST_MALICIOUS_PATH, low_memory=False)
    if dataset:
        return create_dataset(ae_testing_malicious, loader=False)
    return ae_testing_malicious

def get_ae_features_training(dataset=False) -> pd.DataFrame:
    ae_training = pd.read_csv(p.AE_TRAIN_PATH, low_memory=False)
    if dataset:
        return create_dataset(ae_training, loader=False)
    return ae_training

def get_rf_categories_testing() -> pd.DataFrame:
    return pd.read_csv(p.RF_TEST_CATEGORIES_PATH, low_memory=False).iloc[:, 0].values

def get_rf_labels_testing() -> pd.DataFrame:
    return pd.read_csv(p.RF_TEST_LABELS_PATH, low_memory=False).iloc[:, 0].values

def get_rf_features_testing() -> pd.DataFrame:
    return pd.read_csv(p.RF_TEST_PATH, low_memory=False)

def get_rf_categories_training() -> pd.DataFrame:
    return pd.read_csv(p.RF_TRAIN_CATEGORIES_PATH, low_memory=False).iloc[:, 0].values

def get_rf_labels_training() -> pd.DataFrame:
    return pd.read_csv(p.RF_TRAIN_LABELS_PATH, low_memory=False).iloc[:, 0].values

def get_rf_features_training() -> pd.DataFrame:
    return pd.read_csv(p.RF_TRAIN_PATH, low_memory=False)


# <---------- Multiple files in conjunction ---------->
def get_ae_testing(dataset=False) -> dict:
    ae_testing = {
        'ae_testing_benign': get_ae_features_benign_testing(dataset=dataset),
        'ae_testing_malicious': get_ae_features_malicious_testing(dataset=dataset),
    }
    return ae_testing

def get_ae_training(dataset=False) -> dict:
    ae_training = {
        'ae_training': get_ae_features_training(dataset=dataset)
    }
    return ae_training

def get_rf_testing() -> dict:
    rf_testing = {
        'rf_testing': get_rf_features_testing(),
        'rf_labels_testing': get_rf_labels_testing(),
        'rf_categories_testing': get_rf_categories_testing(),
    }
    return rf_testing

def get_rf_training() -> dict:
    rf_training = {
        'rf_training': get_rf_features_training(),
        'rf_labels_training': get_rf_labels_training(),
        'rf_categories_training': get_rf_categories_training(),
    }
    return rf_training


# <---------- Model-level features ---------->
def get_ae_features(dataset=False) -> dict:
    ae_features = {
        **get_ae_testing(dataset=dataset),
        **get_ae_training(dataset=dataset),
    }
    return ae_features

def get_rf_features() -> dict:
    rf_features = {
        **get_rf_testing(),
        **get_rf_training(),
    }
    return rf_features

def get_all_features(dataset=False) -> dict:
    all_features = {
        **get_ae_features(dataset=dataset),
        **get_rf_features(),
    }
    return all_features