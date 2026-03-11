import torch.nn as nn
import torch

from pathlib import Path
BASE_DIR = Path(__file__).parent

# model structure
class AutoEncoder(nn.Module):
    def __init__(self, n_features, dropout=0.1):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 4)
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, n_features)
        )
    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

def construct_model(load=False):
    n_features = 20
    model = AutoEncoder(n_features=n_features)
    if load:
        if not Path(BASE_DIR.parent/'artifacts').exists():
            Path(BASE_DIR.parent/'artifacts').mkdir()

        if not Path(BASE_DIR.parent /'artifacts'/'ae_model.pt').exists():
            from training.ae_train import train_model
            train_model()

        model.load_state_dict(torch.load(BASE_DIR.parent / 'artifacts' / 'ae_model.pt'))
    return model