import pandas as pd
import numpy as np
import ipaddress

def drop(df):
    df.columns = df.columns.str.strip()
    return df.drop(columns=['Timestamp', 'Flow Packets/s', 'Fwd PSH Flags',
       'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
       'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s',
       'Bwd Packets/s', 'Packet Length Std', 'PSH Flag Count', 'URG Flag Count',
       'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
       'Average Packet Size', 'Avg Fwd Segment Size',
       'Avg Bwd Segment Size', 'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk',
       'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
       'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Subflow Fwd Packets',
       'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
       'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
       'act_data_pkt_fwd', 'min_seg_size_forward',
       'Active Std', 'Idle Std', 'Fwd Packet Length Std', 'Bwd Packet Length Std',
       'Flow IAT Std', 'Fwd IAT Std', 'Bwd IAT Std'])

def create_dataframe(paths, label):
    exception_path = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv'
    df = pd.DataFrame()

    for path in paths:
        if path.endswith(exception_path):
            df = pd.concat([df, drop(pd.read_csv(path, encoding='latin1', low_memory=False))], ignore_index=True)
            continue
        df = pd.concat([df, drop(pd.read_csv(path))], ignore_index=True)

    df.to_csv(f'CICIDS2017_{label}.csv', index=False)

    # Data that remains:

    # 'Flow ID', 'Source IP', 'Source Port', 'Destination IP', 'Protocol'

    # 'Flow ID', 'Source IP', 'Source Port', 'Destination IP', 'Destination Port',
    # 'Protocol', 'Flow Duration', 'Flow IAT Max', 'Flow IAT Min', 'Flow IAT Mean',
    # 'Total Fwd Packets', 'Total Backward Packets', 'SYN Flag Count', 'RST Flag Count',
    # 'ACK Flag Count', 'FIN Flag Count', 'Min Packet Length', 'Max Packet Length',
    # 'Packet Length Mean', 'Packet Length Variance', 'Flow Bytes/s'

    # Add to docs:
    # 'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
    # 'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
    # 'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
    # 'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Max', 'Fwd IAT Min',
    # 'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Max', 'Bwd IAT Min'
    # 'Active Mean', 'Active Max', 'Active Min', 'Idle Mean', 'Idle Max', 'Idle Min',

def is_private(ip):
    try:
        return int(ipaddress.ip_network(ip).is_private)
    except:
        return 0

def extract_features_training(df):
    df.columns = df.columns.str.strip()
    fwd = df['Total Fwd Packets']
    bwd = df['Total Backward Packets']
    syn = df['SYN Flag Count']
    ack = df['ACK Flag Count']
    fin = df['FIN Flag Count']
    rst = df['RST Flag Count']
    duration = df['Flow Duration']

    features = pd.DataFrame()

    proto_onehot = pd.get_dummies(df['Protocol'], prefix='proto').astype(np.float32)
    features = pd.concat([features, proto_onehot], axis=1)
    features['Port'] = df['Destination Port'].apply(lambda x: 0 if x <= 1023 else 1 if x <= 49151 else 2)
    features['IP'] = df['Destination IP'].apply(is_private)
    features['Duration'] = duration / 1_000_000
    features['Byte Rate'] = df['Flow Bytes/s']
    features['Packet Rate'] = (fwd + bwd) / (duration + 1e-6)
    features['Forward Rate'] = fwd / (duration + 1e-6)
    features['Backward Rate'] = bwd / (duration + 1e-6)
    features['Min IAT'] = df['Flow IAT Min']
    features['Max IAT'] = df['Flow IAT Max']
    features['Mean IAT'] = df['Flow IAT Mean']
    features['Min Packet Size'] = df['Min Packet Length']
    features['Max Packet Size'] = df['Max Packet Length']
    features['Mean Packet Size'] = df['Packet Length Mean']
    features['Variance Packet Size'] = df['Packet Length Variance']
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

    # put into docs
    features['Forward Packets'] = fwd
    features['Backward Packets'] = bwd
    features['Forward Bytes'] = df['Total Length of Fwd Packets']
    features['Forward Bytes Max'] = df['Fwd Packet Length Max']
    features['Forward Bytes Min'] = df['Fwd Packet Length Min']
    features['Forward Bytes Mean'] = df['Fwd Packet Length Mean']
    features['Forward IAT Total'] = df['Fwd IAT Total']
    features['Forward IAT Max'] = df['Fwd IAT Max']
    features['Forward IAT Min'] = df['Fwd IAT Min']
    features['Forward IAT Mean'] = df['Fwd IAT Mean']
    features['Backward Bytes'] = df['Total Length of Bwd Packets']
    features['Backward Bytes Max'] = df['Bwd Packet Length Max']
    features['Backward Bytes Min'] = df['Bwd Packet Length Min']
    features['Backward Bytes Mean'] = df['Bwd Packet Length Mean']
    features['Backward IAT Total'] = df['Bwd IAT Total']
    features['Backward IAT Max'] = df['Bwd IAT Max']
    features['Backward IAT Min'] = df['Bwd IAT Min']
    features['Backward IAT Mean'] = df['Bwd IAT Mean']
    features['Active Mean'] = df['Active Mean']
    features['Active Max'] = df['Active Max']
    features['Active Min'] = df['Active Min']
    features['Idle Mean'] = df['Idle Mean']
    features['Idle Max'] = df['Idle Max']
    features['Idle Min'] = df['Idle Min']

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)
    features = features.clip(-1e6, 1e6)
    features = features.astype(np.float32)

    labels = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)

    return features, labels