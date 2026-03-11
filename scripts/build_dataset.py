from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from torch import tensor, float32
import joblib as jb
from pathlib import Path

BASE_DIR = Path(__file__).parent

def create_dataset(features, batch_size=2048, loader=True, training=False):
    if not Path(BASE_DIR.parent / 'models' / 'artifacts').exists():
        Path(BASE_DIR.parent / 'models' / 'artifacts').mkdir()

    if training:
        scaler = StandardScaler()
        X_np = scaler.fit_transform(features)
        jb.dump(scaler, BASE_DIR.parent/'models'/'artifacts'/'ae_scaler.pkl')
    else:
        if not Path(BASE_DIR.parent / 'models' / 'artifacts' / 'ae_scaler.pkl').exists():
            from training.ae_train import train_model
            train_model()

        scaler = jb.load(BASE_DIR.parent/'models'/'artifacts'/'ae_scaler.pkl')
        EXPECTED_COLUMNS = list(scaler.feature_names_in_)
        features = features[EXPECTED_COLUMNS]
        X_np = scaler.transform(features)

    X = tensor(X_np, dtype=float32)

    if loader:
        dataset = TensorDataset(X)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        return loader
    return X