from models.definitions.random_forest import construct_model as construct_rf
from retraining.retrain_ae import start_offline_train as retrain_ae
from experiments.structs.ae_feature_list import AE_FEATURES
from datetime import datetime, timezone

import pandas as pd
import experiments.run_experiments as exp
import experiments.scripts.database_handler as dh
import experiments.scripts.paths as p
import shutil

# each poisoned flow db will be the same parent directory and called '(poisoned rate)_poisoned_flows.db'

poison_rates = [0, 1, 2, 5, 10]


def create_poisoned_flows(attack_df, benign_df, n_flows, alpha):
    benign_mean = benign_df[AE_FEATURES].mean()

    sampled = attack_df.sample(n=min(n_flows, len(attack_df)), replace=len(attack_df) < n_flows, random_state=42)

    poisoned = sampled * alpha + benign_mean * (1 - alpha)
    poisoned['rf_category'] = 0
    poisoned['timestamp'] = datetime.now(timezone.utc).isoformat()

    return poisoned


def find_evasion_alpha(attack_features, benign_mean, rf, step=0.05):
    for alpha in [round(1.0 - i * step, 2) for i in range(1, 20)]:
        candidate = attack_features * alpha + benign_mean * (1 - alpha)
        prediction = rf.predict(candidate)
        benign_fraction = (prediction == 0).mean()
        if benign_fraction >= 0.9:
            print(f'Evasion threshold found at alpha={alpha}')
            return alpha
    return 0.1

def get_all_defense_combinations():
    all_combinations = []
    for i in range(2):
        for j in range(2):
            combination = {'Isolation Forest': bool(i), 'Temporal Isolation': False, 'Rollback': bool(j)}
            all_combinations.append(combination)

    return all_combinations


def get_defense_label(defense):
    rollback, iso_forest = defense.get('Rollback', False), defense.get('Isolation Forest', False)
    match (rollback, iso_forest):
        case (True, True):
            return 'rollback and isolation forest'
        case (True, False):
            return 'rollback'
        case (False, True):
            return 'isolation forest'
        case (False, False):
            return 'no defenses'


def generate_poisoned_dbs():
    baseline_benign_csv_path, _, baseline_malicious_csv_path, _ = exp.retrieve_features(label='retrain', target_benign=10000, target_malicious=1000, pcap_save_dir=p.RQ3_PCAP_DIR, csv_save_dir=p.RQ3_CSV_DIR, benign_db_path=p.RQ3_BENIGN_FLOW_DB_PATH)

    baseline_benign_df = pd.read_csv(baseline_benign_csv_path)
    baseline_malicious_df = pd.read_csv(baseline_malicious_csv_path)
    benign_mean = baseline_benign_df.mean()

    rf = construct_rf()
    alpha = find_evasion_alpha(baseline_malicious_df, benign_mean, rf)

    poisoned_dbs = []

    for rate in poison_rates:
        if rate == 0:
            poisoned_dbs.append(p.RQ3_BENIGN_FLOW_DB_PATH)
            continue

        poisoned_db_path = str(p.RQ3_BENIGN_FLOW_DB_PATH).replace('benign', f'{rate}_poisoned')
        poisoned_dbs.append(poisoned_db_path)
        shutil.copy(p.RQ3_BENIGN_FLOW_DB_PATH, poisoned_db_path)

        n_poisoned = int(10000 * rate / 100)
        poisoned_flows = create_poisoned_flows(baseline_benign_df, baseline_malicious_df, n_poisoned, alpha)
        dh.inject_poisoned_flows(poisoned_db_path, poisoned_flows)

    return poisoned_dbs


def retrain_and_get_rollback_results(defense):
    rollback_results = retrain_ae(defenses=defense)

    if rollback_results is None:
        return None, None
    else:
        return rollback_results


def evaluate_model_on_poison_rate(poison_rate, results):
    for defense in get_all_defense_combinations():
        p.restore_artifacts()
        p.copy_artifacts()

        drifted, rolled_back = retrain_and_get_rollback_results(defense)
        sub_result = exp.get_evaluation_results(fail_msg=f'Evaluation on {poison_rate}% poison failed.')

        defense_results = {'Drifted': drifted, 'Rolled Back': rolled_back}
        defense_label = get_defense_label(defense)

        results[f'{defense_label} with {poison_rate}% poison rate'] = {'Defense Results': defense_results, **sub_result}


def run_rq3(experiment_id='RQ3.VM.*'):
    p.copy_sys_db()
    p.copy_artifacts()

    try:
        results = {}
        poisoned_dbs = generate_poisoned_dbs()
        for rate, db in zip(poison_rates, poisoned_dbs):
            p.experimental_to_sys(db)
            evaluate_model_on_poison_rate(rate, results)

        description = f'Evaluation of the auto-encoder with various defenses and poison rates.'
        dh.log_experiment(description, experiment_id, results)
    except Exception as e:
        print(f'Error running rq3: {e}')
    finally:
        p.restore_sys_db()
        p.restore_artifacts()
