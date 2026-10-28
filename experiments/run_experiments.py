from sklearn.metrics import classification_report
import pandas as pd
import experiments.scripts.paths as p
import json


# <---------- Misc Helper Functions (to be used by other experiment files) ---------->
def retrieve_features(pcap_save_dir, csv_save_dir, label='*', malicious_db_path=None, benign_db_path=None, target_benign=5000, target_malicious=500):
    from experiments.scripts.extract_pcap import extract_pcap
    from experiments.scripts.log_pcap import log_pcap

    benign_flow_count, malicious_flow_count = (0, 0) # setting so these values get replaced and default to 0

    # handle malicious traffic
    if target_malicious:
        input('Press a key to continue. Hook up attack simulator.')

        malicious_pcap_path, malicious_flow_count = log_pcap(output_dir=pcap_save_dir, target_flows=target_malicious, label=f'{label}_malicious')
        extract_pcap(pcap_path=malicious_pcap_path, csv_save_dir=csv_save_dir, label=f'{label}_malicious', db_path=malicious_db_path)

        input('Press a key to continue. Disable attack simulator.')

    if target_benign:
        print('Beginning feature retrieval...')

        benign_pcap_path, benign_flow_count = log_pcap(output_dir=pcap_save_dir, target_flows=target_benign, label=f'{label}_benign')
        extract_pcap(pcap_path=benign_pcap_path, csv_save_dir=csv_save_dir, label=f'{label}_benign', db_path=benign_db_path)

        print('Finished feature retrieval.')

    benign_csv_path = csv_save_dir / f'{label}_benign.csv'
    malicious_csv_path = csv_save_dir / f'{label}_malicious.csv'

    return benign_csv_path, benign_flow_count, malicious_csv_path, malicious_flow_count


def get_evaluation_results(fail_msg=''):
    from evaluation.ae_eval import evaluate_model
    results = evaluate_model(return_eval=True, features_benign_path=p.BENIGN_VALIDATION_CSV_PATH, features_malicious_path=p.MALICIOUS_VALIDATION_CSV_PATH)
    if results is None:
        raise Exception(fail_msg)

    truth, predictions, categorical_eval = results
    return {'Classification Report': classification_report(truth, predictions, output_dict=True),
            'Categorical Evaluation': categorical_eval}


def create_cicids_features():
    import experiments.scripts.paths as p
    from util.paths import RAW_CICIDS_PATHS
    from features.extract_training import extract_features_ae as extract_ae, extract_features_rf as extract_rf

    all_df = pd.DataFrame()
    for path in RAW_CICIDS_PATHS:
        df = pd.read_csv(path, encoding='latin1', low_memory=False)
        df.columns = df.columns.str.strip()
        all_df = pd.concat([all_df, df], ignore_index=True)
        all_df = all_df.dropna(subset=['Label'])

    from sklearn.model_selection import train_test_split
    _, test_df = train_test_split(
        all_df,
        test_size=0.3,
        stratify=all_df['Label'],
        random_state=42)

    print('Extracting ae features from CICIDS dataset...')
    ae_cicids_features = extract_ae(test_df, experiment=True)
    ae_cicids_features.to_csv(p.AE_CICIDS_FEATURES_PATH, index=False)

    print('Extracting rf features from CICIDS dataset...')
    rf_cicids_features = extract_rf(test_df, experiment=True)
    rf_cicids_features.to_csv(p.RF_CICIDS_FEATURES_PATH, index=False)


def get_validation():
    _, benign_validation_count, _, malicious_validation_count = retrieve_features(pcap_save_dir=p.VALIDATION_DIR, csv_save_dir=p.VALIDATION_DIR, label='validation')
    validation_count_dict = {'benign': benign_validation_count, 'malicious': malicious_validation_count}

    with open(p.VALIDATION_COUNTS_PATH, 'w') as f:
        json.dump(validation_count_dict, f)



def get_validation_counts():
    with open(p.VALIDATION_COUNTS_PATH) as f:
        validation_count_dict = json.load(f)

    return validation_count_dict.values()


def run_all_experiments(id, vm_num=None):
    from bq1 import run_bq1
    from rq1 import run_rq1
    from rq2 import run_rq2
    from rq3 import run_rq3

    run_bq1(experiment_id=f'BQ1.{id}')
    if vm_num is not None:


        run_rq1(experiment_id=f'RQ1.{vm_num}.{id}')
        run_rq2(experiment_id=f'RQ2.{vm_num}.{id}')
        run_rq3(experiment_id=f'RQ3.{vm_num}.{id}')


if __name__ == '__main__':
    run_all_experiments(id='01', vm_num='0')

    from experiments.scripts.database_handler import view_experiment_table
    view_experiment_table()