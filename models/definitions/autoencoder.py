import torch.nn as nn
import torch

from pathlib import Path
BASE_DIR = Path(__file__).parent

# model structure
class AutoEncoder(nn.Module):
    def __init__(self, n_features):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16)
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, n_features)
        )
    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

# meant to be used FROM other files. Do not run from this local file; it will not find the artifact
def construct_model(load=True):
    n_features = 20
    model = AutoEncoder(n_features=n_features)
    if load:
        model.load_state_dict(torch.load(BASE_DIR.parent/'artifacts'/'ae_model.pt'))
    return model