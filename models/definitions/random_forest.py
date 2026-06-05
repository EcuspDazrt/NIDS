import joblib as jb
import util.paths as p

def construct_model():
    if not p.rf_exists():
        return None
    rf = jb.load(p.RF_MODEL_PATH)
    return rf

def get_predictions(rf, rf_binary_threshold, features):
    proba = rf.predict_proba(features)[:,1]
    predictions = (proba > rf_binary_threshold).astype(int)

    return proba, predictions