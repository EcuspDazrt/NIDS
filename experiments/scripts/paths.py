import shutil
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
EXPERIMENTS_DIR = BASE_DIR / 'experiments'

# <---------- Directories ---------->
SYS_DATA_DIR = BASE_DIR / 'data'
SYS_DATASETS_DIR = BASE_DIR / 'datasets'
SYS_PCAP_DIR = SYS_DATASETS_DIR / 'pcaps'
UNSWNB_DIR = SYS_DATASETS_DIR / 'UNSW-NB15'
VALIDATION_DIR = EXPERIMENTS_DIR / 'validation'

CSV_DIR = EXPERIMENTS_DIR / 'csv\'s'
BQ1_CSV_DIR = CSV_DIR / 'BQ1'
RQ1_CSV_DIR = CSV_DIR / 'RQ1'
RQ2_CSV_DIR = CSV_DIR / 'RQ2'
RQ3_CSV_DIR = CSV_DIR / 'RQ3'

PCAP_DIR = EXPERIMENTS_DIR / 'pcaps'
RQ1_PCAP_DIR = PCAP_DIR / 'RQ1'
RQ2_PCAP_DIR = PCAP_DIR / 'RQ2'
RQ3_PCAP_DIR = PCAP_DIR / 'RQ3'

LOGGING_DIR = EXPERIMENTS_DIR / 'logging'
RQ1_LOGGING_DIR = LOGGING_DIR / 'rq1'
RQ2_LOGGING_DIR = LOGGING_DIR / 'rq2'
RQ3_LOGGING_DIR = LOGGING_DIR / 'rq3'

ALL_DIRS = [
    VALIDATION_DIR,
    CSV_DIR,
    BQ1_CSV_DIR,
    RQ1_CSV_DIR,
    RQ2_CSV_DIR,
    RQ3_CSV_DIR,
    PCAP_DIR,
    RQ1_PCAP_DIR,
    RQ2_PCAP_DIR,
    RQ3_PCAP_DIR,
    LOGGING_DIR,
    RQ1_LOGGING_DIR,
    RQ2_LOGGING_DIR,
]

# <---------- Individual paths ---------->
EXPERIMENT_DB_PATH = EXPERIMENTS_DIR / 'experiments.db'


AE_CICIDS_FEATURES_PATH = BQ1_CSV_DIR / 'ae_cicids.csv'
RF_CICIDS_FEATURES_PATH = BQ1_CSV_DIR / 'rf_cicids.csv'
AE_UNSWNB_FEATURES_PATH = BQ1_CSV_DIR / 'ae_unsw-nb.csv'
RF_UNSWNB_FEATURES_PATH = BQ1_CSV_DIR / 'rf_unsw-nb.csv'
AE_UNSWNB_LABELED_FEATURES_PATH = BQ1_CSV_DIR / 'ae_unsw-nb_labeled.csv'
RF_UNSWNB_LABELED_FEATURES_PATH = BQ1_CSV_DIR / 'rf_unsw-nb_labeled.csv'
UNSWNB_GROUND_TRUTH_PATH = BQ1_CSV_DIR / 'unswnb_gt.csv'

BENIGN_VALIDATION_CSV_PATH = VALIDATION_DIR / 'validation_benign.csv'
MALICIOUS_VALIDATION_CSV_PATH = VALIDATION_DIR / 'validation_malicious.csv'
VALIDATION_COUNTS_PATH = VALIDATION_DIR / 'validation_counts.json'

RQ1_BENIGN_FLOW_DB_PATH = RQ1_LOGGING_DIR / 'benign_flows.db'
RQ2_BENIGN_FLOW_DB_PATH = RQ2_LOGGING_DIR / 'benign_flows.db'
RQ3_BENIGN_FLOW_DB_PATH = RQ3_LOGGING_DIR / 'benign_flows.db'

SYS_DB_PATH =  SYS_DATA_DIR / 'nids_flows.db'
SYS_DB_COPY_PATH = SYS_DATA_DIR / 'nids_flows_copy.db'



# <----------- Helper funcs ---------->
def make_dirs():
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def cicids_features_exist():
    if AE_CICIDS_FEATURES_PATH.exists() and RF_CICIDS_FEATURES_PATH.exists():
        return True
    print('CICIDS csv\'s do not exist. Retrieving Files...')
    try:
        from experiments.run_experiments import create_cicids_features
        create_cicids_features()
        return True
    except Exception as e:
        print(f'Could not generate cicids features. Stopping experiment: {e}')
        return False


def unswnb_features_exist():
    if AE_UNSWNB_LABELED_FEATURES_PATH.exists() and RF_UNSWNB_LABELED_FEATURES_PATH.exists():
        return True
    print('UNSW-NB15 csv\'s do not exist. Retrieving Files...')
    try:
        from experiments.scripts.extract_pcap import extract_pcap
        from experiments.scripts.label_csv import label_csv
        extract_pcap(pcap_path=UNSWNB_DIR, csv_save_dir=BQ1_CSV_DIR, label='unsw-nb', save_rf=True)
        label_csv(AE_UNSWNB_FEATURES_PATH, UNSWNB_GROUND_TRUTH_PATH)
        label_csv(RF_UNSWNB_FEATURES_PATH, UNSWNB_GROUND_TRUTH_PATH)
        return True
    except Exception as e:
        print(f'Could not generate unswnb features. Stopping experiment: {e}')


def validation_exists():
    if BENIGN_VALIDATION_CSV_PATH.exists() and MALICIOUS_VALIDATION_CSV_PATH.exists():
        return True
    print('Validation csv\'s do not exist. Retrieving Files...')
    try:
        from experiments.run_experiments import get_validation
        get_validation()
        return True
    except Exception as e:
        print(f'Could not retrieve validation csvs. Stopping experiment: {e}')




# <---------- Database Handling ---------->
def copy_sys_db():
    if SYS_DB_PATH.exists():
        shutil.copy(SYS_DB_PATH, SYS_DB_COPY_PATH)

def restore_sys_db():
    shutil.copy(SYS_DB_COPY_PATH, SYS_DB_PATH)

def experimental_to_sys(experimental_db):
    shutil.copy(experimental_db, SYS_DB_PATH)


# <---------- Artifact Handling ---------->
artifact = BASE_DIR / 'models' / 'artifacts'
artifacts = [
    artifact / 'ae_model.pt',
    artifact / 'ae_scaler.pkl',
    artifact / 'thresholds.json',
    SYS_DATA_DIR / 'nids_retraining.log',
    SYS_DATA_DIR / 'nids_drift_check.log',
]

def copy_artifacts():
    for art in artifacts:
        art_copy = art.with_stem(art.stem + '_copy')
        shutil.copy(art, art_copy)

def restore_artifacts():
    for art in artifacts:
        art_copy = art.with_stem(art.stem + '_copy')
        shutil.copy(art_copy, art)
        art_copy.unlink()


make_dirs()
