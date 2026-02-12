import torch.nn as nn
import torch

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


def construct_model(load=True):
    n_features = 21
    model = AutoEncoder(n_features=n_features)
    if load:
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parents[2]

        model.load_state_dict(torch.load(f'{BASE_DIR}/models/flow_model.pt'))
    return model
