import pandas as pd
import torch.nn as nn
import torch.optim as optim
import torch
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from torch.utils.data import TensorDataset, DataLoader

from training_features import extract_features_training as extract, create_dataframe as create_df

BASE_DIR = Path(__file__).resolve().parents[1]
paths_training = [f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv',
                  f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv',
                  f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv',
                  f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv']

paths_testing = [f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Tuesday-WorkingHours.pcap_ISCX.csv',
                 f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Wednesday-workingHours.pcap_ISCX.csv',
                 f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Morning.pcap_ISCX.csv',
                 f'{BASE_DIR}/datasets/GeneratedLabelledFlows/TrafficLabelling/Monday-WorkingHours.pcap_ISCX.csv'
                 ]

epochs = 250

class FlowNet(nn.Module):
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

# print('Creating training dataframe...')
# create_df(paths_training, 'training')
# print('Created training dataframe')

# print('Creating testing dataframe...')
# create_df(paths_testing, 'testing_malicious_only', handle_benign='DROP')
# print('Created testing dataframe')

print('Extracting training features...\n')
features = extract(pd.read_csv('CICIDS2017_training_benign_only.csv', low_memory=False))
print('Finished extracting training features\n\nScaling features and creating model...\n')

scaler = StandardScaler()

X_np = scaler.fit_transform(features.values)
X = torch.tensor(X_np, dtype=torch.float32)

dataset = TensorDataset(X)
batch_size = 2048
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

model = FlowNet(n_features=features.shape[1])
model.load_state_dict(torch.load("flow_model.pt"))

criterion = nn.MSELoss(reduction='mean')
optimizer = optim.Adam(model.parameters(), lr=1e-4)
print('Finished scaling features and creating model\n')


print('Training...\n')
for epoch in range(epochs):
    for batch in loader:
        x_batch = batch[0]

        recon = model(x_batch)
        loss = criterion(recon, x_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print(f'Epochs: {epoch + 1} / {epochs}, Loss: {loss.item():.6f}')
        torch.save(model.state_dict(), 'flow_model.pt')
print('Finished training\n')


print('Extracting testing features and labels...\n')
features_malicious = extract(pd.read_csv('CICIDS2017_testing_malicious_only.csv', low_memory=False))
features_benign = extract(pd.read_csv('CICIDS2017_testing_benign_only.csv', low_memory=False))
print('Finished extracting testing features and labels\n\nScaling features and creating model...\n')

X_np = scaler.fit_transform(features_benign.values)
X = torch.tensor(X_np, dtype=torch.float32)
print('Finished scaling features and creating model\n')

print('Running eval...\n')
model.eval()

with torch.no_grad():
    recon = model(X)
    error = ((X - recon) ** 2).mean(dim=1)
    out = error.mean().item()
    print(round(out * 100, 1), '%')

print('Finished eval\n')