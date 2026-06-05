import util.paths as p
import pandas as pd
import torch.nn as nn
import torch

# model structure
class AutoEncoder(nn.Module):
    def __init__(self, n_features, dropout=0.1, layer_1=32, layer_2=16, layer_3=8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, layer_1),
            nn.BatchNorm1d(layer_1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(layer_1, layer_2),
            nn.BatchNorm1d(layer_2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(layer_2, layer_3)
        )
        self.decoder = nn.Sequential(
            nn.Linear(layer_3, layer_2),
            nn.ReLU(),
            nn.Linear(layer_2, layer_1),
            nn.ReLU(),
            nn.Linear(layer_1, n_features)
        )
    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

def construct_model(load=False, l1=32, l2=16, l3=8):
    n_features = 20
    model = AutoEncoder(n_features=n_features, layer_1=l1, layer_2=l2, layer_3=l3)
    if load:
        if not p.ae_exists():
            return None
        model.load_state_dict(torch.load(p.AE_WEIGHTS_PATH))

    return model

def get_error(ae, x):
    if isinstance(x, pd.DataFrame):
        x = torch.tensor(x.values, dtype=torch.float32)
    elif not isinstance(x, torch.Tensor):
        x = torch.tensor(x, dtype=torch.float32)

    with torch.no_grad():
        recon = ae(x)
        error = ((x - recon) ** 2).mean(dim=1).numpy()
    return error