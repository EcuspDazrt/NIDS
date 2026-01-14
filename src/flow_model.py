import time
import pandas as pd
import numpy as np
import ipaddress
import torch.nn as nn
import torch.optim as optim
import torch


def drop(df):
    return df.drop(columns=[' Timestamp', ' Flow Packets/s', 'Fwd PSH Flags',
       ' Bwd PSH Flags', ' Fwd URG Flags', ' Bwd URG Flags',
       ' Fwd Header Length', ' Bwd Header Length', 'Fwd Packets/s',
       ' Bwd Packets/s', ' Packet Length Std', ' PSH Flag Count', ' URG Flag Count',
       ' CWE Flag Count', ' ECE Flag Count', ' Down/Up Ratio',
       ' Average Packet Size', ' Avg Fwd Segment Size',
       ' Avg Bwd Segment Size', ' Fwd Header Length.1', 'Fwd Avg Bytes/Bulk',
       ' Fwd Avg Packets/Bulk', ' Fwd Avg Bulk Rate', ' Bwd Avg Bytes/Bulk',
       ' Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Subflow Fwd Packets',
       ' Subflow Fwd Bytes', ' Subflow Bwd Packets', ' Subflow Bwd Bytes',
       'Init_Win_bytes_forward', ' Init_Win_bytes_backward',
       ' act_data_pkt_fwd', ' min_seg_size_forward',
       ' Active Std', ' Idle Std', ' Fwd Packet Length Std', ' Bwd Packet Length Std',
       ' Flow IAT Std', ' Fwd IAT Std', ' Bwd IAT Std'])

def create_dataframe():
    friday_path_1 = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'
    friday_path_2 = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv'
    friday_path_3 = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Morning.pcap_ISCX.csv'
    monday_path = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Monday-WorkingHours.pcap_ISCX.csv'
    thursday_path_1 = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv'
    thursday_path_2 = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv'
    tuesday_path = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Tuesday-WorkingHours.pcap_ISCX.csv'
    wednesday_path = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Wednesday-workingHours.pcap_ISCX.csv'

    df1 = drop(pd.read_csv(friday_path_1))
    df2 = drop(pd.read_csv(friday_path_2))
    df3 = drop(pd.read_csv(friday_path_3))
    df4 = drop(pd.read_csv(monday_path))
    df5 = drop(pd.read_csv(thursday_path_1))
    df6 = pd.read_csv(thursday_path_2, encoding='latin1', low_memory=False)
    df7 = drop(pd.read_csv(tuesday_path))
    df8 = drop(pd.read_csv(wednesday_path))

    df = pd.concat([df1, df2, df3, df4, df5, df6, df7, df8], ignore_index=True)
    df.to_csv('CICIDS2017_full.csv', index=False)

    # Data that remains:
    # 'Flow ID', ' Source IP', ' Source Port', ' Destination IP', ' Destination Port',
    # ' Protocol', ' Flow Duration', ' Flow IAT Max', ' Flow IAT Min', ' Flow IAT Mean',
    # ' Total Fwd Packets', ' Total Backward Packets', ' SYN Flag Count', ' RST Flag Count',
    # ' ACK Flag Count', 'FIN Flag Count', ' Min Packet Length', ' Max Packet Length',
    # ' Packet Length Mean', ' Packet Length Variance', 'Flow Bytes/s'

    # ' Fwd Packet Length Max', ' Fwd Packet Length Min', ' Fwd Packet Length Mean',
    # 'Bwd Packet Length Max', ' Bwd Packet Length Min', ' Bwd Packet Length Mean',
    # 'Total Length of Fwd Packets', ' Total Length of Bwd Packets',
    # 'Fwd IAT Total', ' Fwd IAT Mean', ' Fwd IAT Max', ' Fwd IAT Min',
    # 'Bwd IAT Total', ' Bwd IAT Mean', ' Bwd IAT Max', ' Bwd IAT Min'
    # 'Active Mean', ' Active Max', ' Active Min', 'Idle Mean', ' Idle Max', ' Idle Min',

def is_private(ip):
    try:
        return int(ipaddress.ip_network(ip).is_private)
    except:
        return 0

def extract_features_training(df):
    df.columns = df.columns.str.strip()
    fwd = df[' Total Fwd Packets']
    bwd = df[' Total Backward Packets']
    syn = df[' SYN Flag Count']
    ack = df[' ACK Flag Count']
    fin = df['FIN Flag Count']
    rst = df[' RST Flag Count']
    duration = df[' Flow Duration']

    features = pd.DataFrame()

    proto_onehot = pd.get_dummies(df[' Protocol'], prefix='proto')
    features = pd.concat([features, proto_onehot], axis=1)
    features['Port'] = df[' Destination Port'].apply(lambda x: 0 if x <= 1023 else 1 if x <= 49151 else 2)
    features['IP'] = df[' Destination IP'].apply(is_private)
    features['Duration'] = duration / 1_000_000
    features['Duration'] = features['Duration'].replace(0, np.nan)
    features['Byte Rate'] = df['Flow Bytes/s']
    features['Packet Rate'] = (fwd + bwd) / (duration + 1e-6)
    features['Forward Rate'] = fwd / (duration + 1e-6)
    features['Backward Rate'] = bwd / (duration + 1e-6)
    features['Min IAT'] = df[' Flow IAT Min']
    features['Max IAT'] = df[' Flow IAT Max']
    features['Mean IAT'] = df[' Flow IAT Mean']
    features['Min Packet Size'] = df[' Min Packet Length']
    features['Max Packet Size'] = df[' Max Packet Length']
    features['Mean Packet Size'] = df[' Packet Length Mean']
    features['Variance Packet Size'] = df[' Packet Length Variance']
    features['In/Out Ratio'] = fwd / (bwd + 1e-6)
    features['Byte/Packet Ratio'] = (df['Flow Bytes/s'] * duration) / (fwd + bwd)
    features['Syn Ratio'] = syn / (fwd + bwd)
    features['Ack Ratio'] = ack / (fwd + bwd)
    features['Fin Ratio'] = fin / (fwd + bwd)
    features['Rst Ratio'] = rst / (fwd + bwd)
    features['Syn Rate'] = syn / (duration + 1e-6)
    features['Ack Rate'] = ack / (duration + 1e-6)
    features['Fin Rate'] = fin / (duration + 1e-6)
    features['Rst Rate'] = rst / (duration + 1e-6)
    features['Syn/Ack Ratio'] = syn / (ack + 1e-6)
    features['Fin/Ack Ratio'] = fin / (ack + 1e-6)
    features['Rst/Syn Ratio'] = rst / (syn + 1e-6)

    features['Forward Packets'] = fwd
    features['Backward Packets'] = bwd
    features['Forward Bytes'] = df['Total Length of Fwd Packets']
    features['Forward Bytes Max'] = df[' Fwd Packet Length Max']
    features['Forward Bytes Min'] = df[' Fwd Packet Length Min']
    features['Forward Bytes Mean'] = df[' Fwd Packet Length Mean']
    features['Forward IAT Total'] = df['Fwd IAT Total']
    features['Forward IAT Max'] = df[' Fwd IAT Max']
    features['Forward IAT Min'] = df[' Fwd IAT Min']
    features['Forward IAT Mean'] = df[' Fwd IAT Mean']
    features['Backward Bytes'] = df[' Total Length of Bwd Packets']
    features['Backward Bytes Max'] = df['Bwd Packet Length Max']
    features['Backward Bytes Min'] = df[' Bwd Packet Length Min']
    features['Backward Bytes Mean'] = df[' Bwd Packet Length Mean']
    features['Backward IAT Total'] = df['Bwd IAT Total']
    features['Backward IAT Max'] = df[' Bwd IAT Max']
    features['Backward IAT Min'] = df[' Bwd IAT Min']
    features['Backward IAT Mean'] = df[' Bwd IAT Mean']
    features['Active Mean'] = df['Active Mean']
    features['Active Max'] = df[' Active Max']
    features['Active Min'] = df[' Active Min']
    features['Idle Mean'] = df['Idle Mean']
    features['Idle Max'] = df[' Idle Max']
    features['Idle Min'] = df[' Idle Min']

    features = features.apply(pd.to_numeric, errors='coerce')  # convert anything non-numeric to NaN
    features = features.fillna(0)

    labels = df[' Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)

    return features, labels

epochs = 100

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

# print('Creating the dataframe...')
# create_dataframe()
print('Extracting features and labels...')
features, labels = extract_features_training(pd.read_csv('CICIDS2017_full.csv', low_memory=False))
print('Extracted features and labels...')

X = torch.tensor(features.values, dtype=torch.float32)
Y = torch.tensor(labels.values, dtype=torch.float32).unsqueeze(1)

model = FlowNet(n_features=features.shape[1])
# model.load_state_dict(torch.load("flow_model.pt"))
num_pos = (Y==1).sum()
num_neg = (Y==0).sum()
pos_weight = num_neg / num_pos
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = optim.Adam(model.parameters(), lr=1e-3)

print('Training...')
for epoch in range(epochs):
    print(f'Epochs: {epoch + 1} / {epochs}')
    y_prediction = model(X)
    loss = criterion(y_prediction, Y)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

print('Finished training...\nRunning testing...')

model.eval()
true_positive = 0
true_negative = 0
false_positive = 0
false_negative = 0
threshold = 0.5

with torch.no_grad():
    for x, y in zip(X, Y):
        risk = torch.sigmoid(model(x))
        guess = round(risk.item(), 2)
        label = 'Malicious' if y == 1 else 'Benign'
        if label == 'Malicious':
            if guess > threshold:
                true_positive += 1
            else:
                false_negative += 1
        else:
            if guess > threshold:
                false_positive += 1
            else:
                true_negative += 1
print('Finished testing...')
print(f'True Positive: {true_positive}\nFalse Positive: {false_positive}\nTrue Negative: {true_negative}\nFalse Negative: {false_negative}')
print(f'Precision: {round((true_positive / (true_positive + false_positive)) * 100, 2)}%\nRecall: {round((true_positive / (true_positive + false_negative)) * 100, 2)}%')

torch.save(model.state_dict(), 'flow_model.pt')
