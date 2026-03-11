import pandas as pd
import json
from sklearn.metrics import classification_report

from models.definitions.random_forest import construct_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

def evaluate_model():
    rf = construct_model()

    if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
        from scripts.calibrate_thresholds import calibrate_thresholds
        calibrate_thresholds()

    with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
        t = json.load(f)
    rf_binary_threshold = t['rf_binary']

    X_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_testing.csv')
    Y_test = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_testing.csv')

    proba = rf.predict_proba(X_test.to_numpy())[:,1]
    Y_pred = (proba > rf_binary_threshold).astype(int)

    print(classification_report(Y_test, Y_pred))

if __name__ == '__main__':
    evaluate_model()