from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from torch import tensor, float32
import joblib as jb

def create_dataset(features, batch_size=0, loader=True, training=False):
    if training:
        scaler = StandardScaler()
        X_np = scaler.fit_transform(features)
        jb.dump(scaler, '../models/artifacts/ae_scaler.pkl')
    else:
        scaler = jb.load("../models/artifacts/ae_scaler.pkl")
        EXPECTED_COLUMNS = list(scaler.feature_names_in_)
        features = features[EXPECTED_COLUMNS]
        X_np = scaler.transform(features)

    X = tensor(X_np, dtype=float32)

    if loader:
        dataset = TensorDataset(X)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        return loader
    return X