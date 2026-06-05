from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from torch import tensor, float32
import joblib as jb
import util.paths as p


def create_scaler():
    scaler = StandardScaler()
    jb.dump(scaler, p.AE_SCALER_PATH)


def tensor_to_loader(final_features, batch_size):
    dataset = TensorDataset(final_features)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    return loader


def create_dataset(features, batch_size=2048, loader=True, update_scaler=False):
    if not p.ae_scaler_exists():
        return None

    if update_scaler:
        create_scaler()

    scaler = jb.load(p.AE_SCALER_PATH)
    expected_columns = list(scaler.feature_names_in_)

    features = features[expected_columns]
    transformed_features = scaler.transform(features)
    final_features = tensor(transformed_features, dtype=float32)

    if loader:
        return tensor_to_loader(final_features, batch_size)
    return final_features
