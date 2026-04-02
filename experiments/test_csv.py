# takes in any .csv file that is labeled and returns the evaluation results based on the ae.eval file to be used on the extracted pcap features
import pandas as pd
from sklearn.metrics import classification_report
from evaluation.ae_eval import evaluate_model as eval_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

def test_csv(path=None):
    if path is None:
        print('No path received...')
        return

    features = pd.read_csv(path, low_memory=False)
    col_lower = {col.lower().strip(): col for col in features.columns}
    label = col_lower.get('label') or col_lower.get('labels')
    if label is None:
        print('No label received...')
        return

    features['_binary_label'] = (features[label] != 'BENIGN') & (features[label] != 0)
    features_benign = features[features['_binary_label'] == False].drop([label, '_binary_label'], axis=1)
    features_malicious = features[features['_binary_label'] == True].drop([label, '_binary_label'], axis=1)

    benign_path = str(path).replace('.csv', '_benign.csv')
    malicious_path = str(path).replace('.csv', '_malicious.csv')

    features_benign.to_csv(benign_path, index=False)
    features_malicious.to_csv(malicious_path, index=False)

    results = eval_model(return_eval=True, features_benign_path=benign_path, features_malicious_path=malicious_path)
    if not results:
        print('No results available...')
        return

    y_pred, binary_predictions, categorical_eval = results
    print(classification_report(y_pred, binary_predictions))
    print(categorical_eval)

if __name__ == '__main__':
    test_csv() #input file name