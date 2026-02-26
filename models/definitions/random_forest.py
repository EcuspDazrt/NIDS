import joblib as jb

# meant to be used FROM other files. Do not run from this local file; it will not find the artifact
def construct_model():
    rf = jb.load('../models/artifacts/rf_model.pkl')
    return rf