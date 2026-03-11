import joblib as jb
from pathlib import Path
BASE_DIR = Path(__file__).parent

def construct_model():
    if not Path(BASE_DIR.parent / 'artifacts').exists():
        Path(BASE_DIR.parent / 'artifacts').mkdir()

    if not Path(BASE_DIR.parent/'artifacts'/'rf_model.pkl').exists():
        from training.rf_train import create_model
        create_model()

    rf = jb.load(BASE_DIR.parent/'artifacts'/'rf_model.pkl')
    return rf