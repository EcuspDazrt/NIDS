# Designed to be lightweight and only used for filtering. All instances of the isolation forest will ONLY depend on this file.
from sklearn.ensemble import IsolationForest
import joblib
import util.paths as p

from util.feature_retrieval import get_ae_features_training
from util.logger import get_logger
LOGGER = get_logger(__name__)


def fit_isolation_forest():
    LOGGER.info('Isolation Forest began training')
    features = get_ae_features_training()

    iso = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )

    iso.fit(features)
    joblib.dump(iso, p.ISO_MODEL_PATH)

    LOGGER.info('Isolation Forest trained successfully')
    return iso

def iso_forest_filter(features_df):
    if not p.ISO_MODEL_PATH.exists():
        fit_isolation_forest()

    iso = joblib.load(p.ISO_MODEL_PATH)
    predictions = iso.predict(features_df) # 1 = normal, -1 = outlier
    return predictions == 1

if __name__ == '__main__':
    fit_isolation_forest()