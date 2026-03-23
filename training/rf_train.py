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

    if not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_training.csv').exists() or not Path(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_training.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    x_train = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_training.csv', low_memory=False)
    y_train = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'rf_labels_training.csv', low_memory=False)['Label'].values

    print('Fitting rf model...')
    rf.fit(x_train, y_train)
    jb.dump(rf, BASE_DIR.parent/'models'/'artifacts'/'rf_model.pkl')

if __name__ == '__main__':
    create_model()