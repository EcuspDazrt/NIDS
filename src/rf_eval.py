import pandas as pd
from sklearn.metrics import classification_report

from models.random_forest import construct_model

def evaluate_model():
    rf = construct_model()

    THRESHOLD = 0.1

    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[1]
    X_test = pd.read_csv(f'{BASE_DIR}/datasets/processed/rf_testing.csv')
    Y_test = pd.read_csv(f'{BASE_DIR}/datasets/processed/rf_labels_testing.csv')

    proba = rf.predict_proba(X_test)[:,1]
    Y_pred = (proba > THRESHOLD).astype(int)

    print(classification_report(Y_test, Y_pred))
