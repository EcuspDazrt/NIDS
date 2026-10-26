from pathlib import Path
from util.logger import get_logger

LOGGER = get_logger(__name__)
BASE_DIR = Path(__file__).parent

# <---------- Directories ---------->
DATA_DIR = BASE_DIR.parent / 'data'
GUI_DIR = BASE_DIR.parent / 'gui'
DATASETS_DIR = BASE_DIR.parent / 'datasets'
PROCESSED_DATASETS_DIR = DATASETS_DIR / 'processed'
AGGREGATED_DATASETS_DIR = DATASETS_DIR / 'Aggregated'
RAW_CICIDS_DIR = DATASETS_DIR / 'CICIDS2017'
ARTIFACTS_DIR = BASE_DIR.parent / 'models' / 'artifacts'
BACKUPS_DIR = ARTIFACTS_DIR / 'retraining_backups'

# <---------- Unnecessary dirs ---------->
MANUAL_BACKUPS_DIR = ARTIFACTS_DIR / 'manual_backups'

# <---------- Data Paths ---------->
FLOW_DB_PATH = DATA_DIR / 'nids_flows.db'
ALERT_DB_PATH = DATA_DIR / 'nids_alerts.db'
ALERT_LOG_PATH = DATA_DIR / 'nids_alerts.log'
RETRAIN_LOG_PATH = DATA_DIR / 'nids_retraining.log'
DRIFT_CHECK_LOG_PATH = DATA_DIR / 'nids_drift_check.log'

# <---------- Resource Paths ---------->
ICON_PATH = GUI_DIR / 'resources' / 'nids_logo.png'
ICON_BITMAP_PATH = GUI_DIR / 'resources' / 'nids_icon.ico'

# <---------- Dataset Paths ---------->
AE_TEST_BENIGN_PATH = PROCESSED_DATASETS_DIR / 'ae_testing_benign.csv'
AE_TEST_MALICIOUS_PATH = PROCESSED_DATASETS_DIR / 'ae_testing_malicious.csv'
AE_TRAIN_PATH = PROCESSED_DATASETS_DIR / 'ae_training.csv'

RF_TEST_CATEGORIES_PATH = PROCESSED_DATASETS_DIR / 'rf_categories_testing.csv'
RF_TEST_LABELS_PATH = PROCESSED_DATASETS_DIR / 'rf_labels_testing.csv'
RF_TEST_PATH = PROCESSED_DATASETS_DIR / 'rf_testing.csv'
RF_TRAIN_CATEGORIES_PATH = PROCESSED_DATASETS_DIR / 'rf_categories_training.csv'
RF_TRAIN_LABELS_PATH = PROCESSED_DATASETS_DIR / 'rf_labels_training.csv'
RF_TRAIN_PATH = PROCESSED_DATASETS_DIR / 'rf_training.csv'

RAW_AE_TEST_BENIGN_PATH = AGGREGATED_DATASETS_DIR / 'CICIDS2017_ae_testing_benign.csv'
RAW_AE_TEST_MALICIOUS_PATH = AGGREGATED_DATASETS_DIR / 'CICIDS2017_ae_testing_malicious.csv'
RAW_AE_TRAIN_PATH = AGGREGATED_DATASETS_DIR / 'CICIDS2017_ae_training.csv'
RAW_RF_TEST_PATH = AGGREGATED_DATASETS_DIR / 'CICIDS2017_rf_testing.csv'
RAW_RF_TRAIN_PATH = AGGREGATED_DATASETS_DIR / 'CICIDS2017_rf_training.csv'

# <---------- Artifact Paths ---------->
THRESHOLDS_PATH = ARTIFACTS_DIR / 'thresholds.json'
BLOCKLIST_PATH = ARTIFACTS_DIR / 'ja3_blocklist.txt'
AE_WEIGHTS_PATH = ARTIFACTS_DIR / 'ae_model.pt'
AE_SCALER_PATH = ARTIFACTS_DIR / 'ae_scaler.pkl'
RF_MODEL_PATH = ARTIFACTS_DIR / 'rf_model.pkl'
ISO_MODEL_PATH = ARTIFACTS_DIR / 'iso_forest.pkl'

# <---------- Compiled pathing lists ---------->
ALL_DIRS = [
    DATA_DIR,
    GUI_DIR,
    DATASETS_DIR,
    PROCESSED_DATASETS_DIR,
    AGGREGATED_DATASETS_DIR,
    RAW_CICIDS_DIR,
    ARTIFACTS_DIR,
    BACKUPS_DIR
]

PROCESSED_DATASETS = [
    AE_TEST_BENIGN_PATH,
    AE_TEST_MALICIOUS_PATH,
    AE_TRAIN_PATH,
    RF_TEST_CATEGORIES_PATH,
    RF_TEST_LABELS_PATH,
    RF_TEST_PATH,
    RF_TRAIN_CATEGORIES_PATH,
    RF_TRAIN_LABELS_PATH,
    RF_TRAIN_PATH,
]

RAW_DATASETS = [
    RAW_AE_TRAIN_PATH,
    RAW_AE_TEST_MALICIOUS_PATH,
    RAW_AE_TRAIN_PATH,
    RAW_RF_TEST_PATH,
    RAW_RF_TRAIN_PATH
]

RAW_CICIDS_PATHS = [
    RAW_CICIDS_DIR / 'Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Friday-WorkingHours-Morning.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Tuesday-WorkingHours.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Wednesday-workingHours.pcap_ISCX.csv',
    RAW_CICIDS_DIR / 'Monday-WorkingHours.pcap_ISCX.csv'
]


# <---------- Handle Dependencies ---------->
def make_dirs():
    for DIR in ALL_DIRS:
        if DIR.exists():
            continue
        DIR.mkdir(parents=True, exist_ok=True)


def make_ae_construction_dir(construction):
    Path.mkdir(ARTIFACTS_DIR / 'manual_backups' / f'{construction}_construction', exist_ok=True, parents=True)


def thresholds_exist():
    if THRESHOLDS_PATH.exists():
        return True
    try:
        from util.thresholds import calibrate_thresholds
        calibrate_thresholds()
        return True
    except Exception:
        LOGGER.exception('could not calculate thresholds')
        return False


def could_train_ae():
    try:
        from training.ae_train import train_most_optimized_model as train_ae
        train_ae()
        return True
    except Exception:
        LOGGER.exception('could not train autoencoder')
        return False


def ae_scaler_exists():
    if AE_SCALER_PATH.exists():
        return True
    return False


def ae_exists():
    if AE_WEIGHTS_PATH.exists() and ae_scaler_exists():
        return True
    return could_train_ae()


def rf_exists():
    if RF_MODEL_PATH.exists():
        return True
    try:
        from training.rf_train import create_model as fit_rf
        fit_rf()
        return True
    except Exception:
        LOGGER.exception('could not create random forest')
        return False


def iso_exists():
    if ISO_MODEL_PATH.exists():
        return True
    try:
        from models.definitions.isolation_forest import fit_isolation_forest as fit_iso
        fit_iso()
        return True
    except Exception:
        LOGGER.exception('could not create isolation forest')
        return False


def blocklist_exists():
    if BLOCKLIST_PATH.exists():
        return True
    LOGGER.error('JA3 blocklist is not available')
    return False


def models_exist():
    if ae_exists() and rf_exists() and iso_exists():
        return True
    return False


def artifacts_exist():
    if models_exist() and blocklist_exists() and thresholds_exist():
        LOGGER.info('all artifacts exist')
        return True
    LOGGER.error('artifacts could not be created')
    return False


def processed_dataset_exists():
    for dataset in PROCESSED_DATASETS:
        if not dataset.exists():
            if not raw_dataset_exists():
                return False
            try:
                from features.extract_training import process_raw_dataset
                process_raw_dataset()
            except Exception:
                LOGGER.exception('unable to process raw dataset')
                return False
    return True


def raw_dataset_exists():
    for dataset in RAW_DATASETS:
        if not dataset.exists():
            if not cicids_dataset_exists():
                return False
            try:
                from scripts.build_dataframe import init_dataframes
                init_dataframes()
            except Exception:
                LOGGER.exception('unable to build dataframes')
                return False
    return True


def cicids_dataset_exists():
    for dataset in RAW_CICIDS_PATHS:
        if not dataset.exists():
            LOGGER.error('raw CICIDS dataset does not exist. requires download.')
            return False
    return True


make_dirs()
