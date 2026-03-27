import torch.nn as nn
import torch

from pathlib import Path
BASE_DIR = Path(__file__).parent

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

def construct_model(load=False, model_name='ae_model', l1=32, l2=16, l3=8):
    n_features = 20
    model = AutoEncoder(n_features=n_features, layer_1=l1, layer_2=l2, layer_3=l3)
    if load:
        if not Path(BASE_DIR.parent/'artifacts').exists():
            Path(BASE_DIR.parent/'artifacts').mkdir()

        if not Path(BASE_DIR.parent /'artifacts'/f'{model_name}.pt').exists():
            from training.ae_train import train_model
            train_model()

        model.load_state_dict(torch.load(BASE_DIR.parent / 'artifacts' / 'ae_model.pt'))
    return model