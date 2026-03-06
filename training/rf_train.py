from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import joblib as jb

from pathlib import Path
BASE_DIR = Path(__file__).parent

def create_model():
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=20,
        class_weight='balanced_subsample',
        n_jobs=-1,
        random_state=42,
    )

    x_train = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_training.csv', low_memory=False)
    y_train = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_training.csv', low_memory=False)['Label'].values

    rf.fit(x_train, y_train)
    jb.dump(rf, BASE_DIR.parent/'models'/'artifacts'/'rf_model.pkl')

create_model()