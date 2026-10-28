from experiments.scripts.test_csv import test_csv
from sklearn.metrics import classification_report

import experiments.scripts.paths as p
import experiments.scripts.database_handler as dh

def run_bq1(experiment_id='BQ1.*'):
    if not p.cicids_features_exist() or not p.unswnb_features_exist():
        return

    print('Evaluating each of the models...')
    truth, predictions, categorical_eval  = test_csv(p.AE_CICIDS_FEATURES_PATH, eval_type='ae', source_type='cicids')
    ae_cicids_results = {'Classification Report': classification_report(truth, predictions, output_dict=True), 'Categorial Eval': categorical_eval}

    truth, predictions, categorical_eval = test_csv(p.AE_UNSWNB_LABELED_FEATURES_PATH, eval_type='ae', source_type='unswnb')
    ae_unswnb_results = {'Classification Report': classification_report(truth, predictions, output_dict=True), 'Categorial Eval': categorical_eval}

    truth, predictions, categorical_eval = test_csv(p.RF_CICIDS_FEATURES_PATH, eval_type='rf', source_type='cicids')
    rf_cicids_results = {'Classification Report': classification_report(truth, predictions, output_dict=True), 'Categorial Eval': categorical_eval}

    truth, predictions, categorical_eval = test_csv(p.RF_UNSWNB_LABELED_FEATURES_PATH, eval_type='rf', source_type='unswnb')
    rf_unswnb_results = {'Classification Report': classification_report(truth, predictions, output_dict=True), 'Categorial Eval': categorical_eval}

    # log experiment results
    print('Logging experiment results...')
    results = {'ae_cicids_results': ae_cicids_results, 'ae_unswnb_results': ae_unswnb_results, 'rf_cicids_results': rf_cicids_results, 'rf_unswnb_results': rf_unswnb_results}
    description = 'Evaluation of the auto-encoder and random forest on the baseline (CICIDS2017)'
    dh.log_experiment(description, experiment_id, results)

if __name__ == '__main__':
    run_bq1()