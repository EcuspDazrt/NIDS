import joblib as jb
from pathlib import Path

# meant to be used FROM other files. Do not run from this local file; it will not find the artifact
def construct_model():
    BASE_DIR = Path(__file__).resolve().parent.parent
    rf = jb.load(BASE_DIR.parent/'models'/'artifacts'/'rf_model.pkl')
    return rf