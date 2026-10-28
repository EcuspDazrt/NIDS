
from retraining.retrain_ae import start_offline_train as retrain_ae

import run_experiments as exp
import experiments.scripts.database_handler as dh
import experiments.scripts.paths as p


def run_retraining():
    exp.retrieve_features(label='retrain', target_benign=10000, target_malicious=0, pcap_save_dir=p.RQ1_PCAP_DIR, csv_save_dir=p.RQ1_CSV_DIR, benign_db_path=p.RQ1_BENIGN_FLOW_DB_PATH)
    p.experimental_to_sys(p.RQ1_BENIGN_FLOW_DB_PATH)
    retrain_ae(defenses={'Isolation Forest': False, 'Temporal Isolation': False, 'Rollback': False})

def compile_experiment_results(experiment_id, pre_train_results, post_train_results):
    benign_validation_count, malicious_validation_count = exp.get_validation_counts()
    final_results = {'Pretraining Results': pre_train_results, 'Post-training Results': post_train_results}
    description = f'Evaluation of the auto-encoder before and after calibrating on live-capture traffic with {benign_validation_count} benign validation samples and {malicious_validation_count} malicious validation samples'
    dh.log_experiment(description, experiment_id, final_results)


def run_rq1(experiment_id='RQ1.VM.*'):
    if not p.validation_exists():
        return

    p.copy_sys_db()
    p.copy_artifacts()

    try:
        pre_train_results = exp.get_evaluation_results()
        run_retraining()
        post_train_results = exp.get_evaluation_results()

        compile_experiment_results(experiment_id, pre_train_results, post_train_results)
    except Exception as e:
        print(f'Error running rq1: {e}')
    finally:
        p.restore_sys_db()
        p.restore_artifacts()