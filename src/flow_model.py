import pandas as pd
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import torch
from pathlib import Path
from sklearn.preprocessing import StandardScaler
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

epochs = 0

class FlowNet(nn.Module):
    def __init__(self, n_features):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
    def forward(self, x):
        return self.net(x)

# print('Creating training dataframe...')
# create_df(paths_training, 'training')
# print('Created training dataframe')

# print('Creating testing dataframe...')
# create_df(paths_testing, 'testing')
# print('Created testing dataframe')

print('Extracting training features and labels...\n')
features, labels = extract(pd.read_csv('CICIDS2017_training.csv', low_memory=False))
print('Finished extracting training features and labels\n\nScaling features and creating model...\n')
scaler = StandardScaler()
X_np = scaler.fit_transform(features.values)
X = torch.tensor(X_np, dtype=torch.float32)
Y = torch.tensor(labels.values, dtype=torch.float32).unsqueeze(1)
dataset = TensorDataset(X, Y)
loader = DataLoader(dataset, batch_size=8192, shuffle=True)

model = FlowNet(n_features=features.shape[1])
model.load_state_dict(torch.load("flow_model.pt"))
num_pos = (Y==1).sum()
num_neg = (Y==0).sum()
pos_weight = torch.clamp(num_neg / num_pos, max=10)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = optim.Adam(model.parameters(), lr=1e-4)
print('Finished scaling features and creating model\n')

print('Training...\n')
for epoch in range(epochs):
    total_loss = 0
    for xb, yb in loader:
        predictions = model(xb)
        loss = criterion(predictions, yb)

        optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0
        )

        optimizer.step()

        total_loss += loss.item()
    print(f'Epochs: {epoch + 1} / {epochs}, Loss: {total_loss:.4f}')
    torch.save(model.state_dict(), 'flow_model.pt')
print('Finished training\n')


print('Extracting testing features and labels...\n')
features, labels = extract(pd.read_csv('CICIDS2017_testing.csv', low_memory=False))
print('Finished extracting testing features and labels\n\nScaling features and creating model...\n')
X_np = scaler.fit_transform(features.values)
X = torch.tensor(X_np, dtype=torch.float32)
Y = torch.tensor(labels.values, dtype=torch.float32).unsqueeze(1)
print('Finished scaling features and creating model\n')

print('Running eval...\n')
model.eval()
guess_map = {(1, True):0, (1, False):0, (0, True): 0, (0, False): 0} # true pos, false neg, false pos, true neg
threshold = 0.2

with torch.no_grad():
    for x, y in zip(X, Y):
        risk = torch.sigmoid(model(x))
        guess = round(risk.item(), 2)
        label = 1 if y == 1 else 0
        guess_map[(label, guess > threshold)] += 1

print('Finished eval\n')
print(f'True Positive: {guess_map[(1, True)]}\nFalse Positive: {guess_map[(0, True)]}\nTrue Negative: {guess_map[(0, False)]}\nFalse Negative: {guess_map[(1, False)]}')
print(f'Precision: {round((guess_map[(1, True)] / (guess_map[(1, True)] + guess_map[(0, True)])) * 100, 2)}%\nRecall: {round((guess_map[(1, True)] / (guess_map[(1, True)] + guess_map[(1, False)])) * 100, 2)}%')
