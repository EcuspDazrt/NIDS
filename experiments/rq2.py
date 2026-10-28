from evaluation.ae_eval import evaluate_model
from retraining.retrain_ae import start_offline_train as retrain_ae
from sklearn.metrics import classification_report
import random, sqlite3

import experiments.run_experiments as exp
import experiments.scripts.paths as p
import experiments.scripts.database_handler as dh

flow_thresholds = [500, 1000, 2500, 3500, 5000, 6500, 7500, 9000, 10000]
max_threshold = flow_thresholds[-1]


def retrieve_ids(db_path, seed=42):
    with sqlite3.connect(db_path) as conn:
        all_ids = [row[0] for row in conn.execute('SELECT id FROM flow_logs ORDER BY id')]
    rng = random.Random(seed)
    rng.shuffle(all_ids)
    return all_ids


def evaluate_model_on_threshold(final_results, all_ids, threshold):
    slice_ids = all_ids[:threshold]
    retrain_ae(defenses={'Isolation Forest': False, 'Temporal Isolation': False, 'Rollback': False}, flow_ids=slice_ids)

    result = evaluate_model(return_eval=True, features_benign_path=p.BENIGN_VALIDATION_CSV_PATH, features_malicious_path=p.MALICIOUS_VALIDATION_CSV_PATH)
    if result is None:
        raise Exception('Threshold evaluation failed: no results returned.')

    truth, prediction, categorical_eval = result
    final_results[threshold] = {'Classification Report': classification_report(truth, prediction, output_dict=True), 'Categorical Evaluation': categorical_eval}
    return result


def get_all_ids():
    exp.retrieve_features(label='retrain', target_benign=max_threshold, target_malicious=0, pcap_save_dir=p.RQ2_PCAP_DIR, csv_save_dir=p.RQ2_CSV_DIR, benign_db_path=p.RQ2_BENIGN_FLOW_DB_PATH)
    p.experimental_to_sys(p.RQ2_BENIGN_FLOW_DB_PATH)
    return retrieve_ids(p.RQ2_BENIGN_FLOW_DB_PATH, seed=42)


def run_rq2(experiment_id='RQ2.VM.*'):
    p.copy_sys_db()
    p.copy_artifacts()
    try:
        final_results = {}

        pre_train_results = exp.get_evaluation_results()
        final_results[0] = pre_train_results

        all_ids = get_all_ids()
        for threshold in flow_thresholds:
            p.restore_artifacts()
            p.copy_artifacts()
            evaluate_model_on_threshold(final_results, all_ids, threshold)

        benign_validation_count, malicious_validation_count = exp.get_validation_counts()
        description = f'Evaluation of the auto-encoder on various flow thresholds with {benign_validation_count} benign validation samples and {malicious_validation_count} malicious validation samples.'
        dh.log_experiment(description, experiment_id, final_results)

    except Exception as e:
        print(f'Error running rq2: {e}')
    finally:
        p.restore_sys_db()
        p.restore_artifacts()
