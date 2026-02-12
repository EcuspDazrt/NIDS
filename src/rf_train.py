from sklearn.ensemble import RandomForestClassifier
from pathlib import Path
import pandas as pd
import joblib as jb

def create_model():
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=20,
        class_weight='balanced_subsample',
        n_jobs=-1,
        random_state=42,
    )

    BASE_DIR = Path(__file__).resolve().parents[1]

    x_train = pd.read_csv(f'{BASE_DIR}/datasets/processed/rf_training.csv', low_memory=False)
    y_train = pd.read_csv(f'{BASE_DIR}/datasets/processed/rf_labels_training.csv', low_memory=False)['Label'].values

    rf.fit(x_train, y_train)
    jb.dump(rf, 'rf_model.pkl')

create_model()