# Designed to be lightweight and only used for filtering. All instances of the isolation forest will ONLY depend on this file.
from sklearn.ensemble import IsolationForest
import joblib
import pandas as pd

from pathlib import Path
BASE_DIR = Path(__file__).parent

def fit_isolation_forest(training_features_path):
    if not training_features_path.exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    df = pd.read_csv(training_features_path)

    iso = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )

    iso.fit(df)
    joblib.dump(iso, BASE_DIR.parent/'artifacts'/'iso_forest.pkl')
    return iso

def iso_forest_filter(features_df):
    if not Path(BASE_DIR.parent/'artifacts'/'iso_forest.pkl').exists():
        fit_isolation_forest(BASE_DIR.parent.parent/'datasets'/'processed'/'ae_training.csv')

    iso = joblib.load(BASE_DIR.parent/'artifacts'/'iso_forest.pkl')
    predictions = iso.predict(features_df) # 1 = normal, -1 = outlier
    return predictions == 1

if __name__ == '__main__':
    fit_isolation_forest(BASE_DIR.parent.parent/'datasets'/'processed'/'ae_training.csv')