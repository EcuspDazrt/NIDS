import joblib as jb

def construct_model():
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[2]

    rf = jb.load(f'{BASE_DIR}/models/rf_model.pkl')

    return rf
