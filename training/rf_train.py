from sklearn.ensemble import RandomForestClassifier
import joblib as jb
import util.paths as p

from util.feature_retrieval import get_rf_features_training, get_rf_labels_training
from util.logger import get_logger
LOGGER = get_logger(__name__)

def create_model():
    LOGGER.info('Rf began training')
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=20,
        class_weight='balanced_subsample',
        n_jobs=-1,
        random_state=42,
    )

    if not p.processed_dataset_exists():
        return

    training_features = get_rf_features_training()
    training_labels = get_rf_labels_training()['Label'].values

    rf.fit(training_features, training_labels)
    jb.dump(rf, p.RF_MODEL_PATH)
    LOGGER.info('Autoencoder finished training')

if __name__ == '__main__':
    create_model()