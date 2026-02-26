import pandas as pd
import numpy as np
import ipaddress

# ae_features = 14
# rf_features = 63

def is_private(ip):
    try:
        return int(ipaddress.ip_network(ip).is_private)
    except:
        return 0

def extract_features_rf(df, label="", save_type=None):
    df.columns = df.columns.str.strip()
    features = pd.DataFrame()

    fwd = df['Total Fwd Packets']
    bwd = df['Total Backward Packets']
    syn = df['SYN Flag Count']
    ack = df['ACK Flag Count']
    fin = df['FIN Flag Count']
    rst = df['RST Flag Count']
    duration = df['Flow Duration']

    all_protocols = [0, 6, 17]
    df['Protocol'] = pd.to_numeric(df['Protocol'], errors='coerce').fillna(0).astype(int)
    df['Protocol'] = pd.Categorical(df['Protocol'], categories=all_protocols)
    proto_onehot = pd.get_dummies(df['Protocol'], prefix='proto', dtype=int)
    features = pd.concat([features, proto_onehot], axis=1)

    features['Port'] = df['Destination Port'].apply(lambda x: 0 if x <= 1023 else 1 if x <= 49151 else 2)
    features['IP'] = df['Destination IP'].apply(is_private)
    features['Duration'] = duration / 1_000_000
    features['In/Out Ratio'] = fwd / (bwd + 1e-6)

    features['Total Packets'] = fwd + bwd
    features['Total Bytes'] = (df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)
    features['Total Packet Rate'] = (fwd + bwd) / (duration + 1e-6)
    features['Total Byte Rate'] = ((df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)) / (duration + 1e-6)
    features['Total Byte Max'] = df[['Fwd Packet Length Max', 'Bwd Packet Length Max']].max(axis=1)
    features['Total Byte Min'] = df[['Fwd Packet Length Min', 'Bwd Packet Length Min']].min(axis=1)
    features['Total Byte Mean'] = ((df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)) / (fwd + bwd)
    features['Total Byte Std'] = df['Packet Length Std']
    features['Total Byte Variance'] = (((features['Total Byte Max'] - features['Total Byte Mean']) ** 2) + ((features['Total Byte Mean'] - features['Total Byte Min']) ** 2)) / 2

    features['Forward Packets'] = fwd
    features['Forward Bytes'] = df['Fwd Packet Length Mean'] * fwd
    features['Forward Packet Rate'] = fwd / (duration + 1e-6)
    features['Forward Byte Rate'] = (df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6)
    features['Forward Byte Max'] = df['Fwd Packet Length Max']
    features['Forward Byte Min'] = df['Fwd Packet Length Min']
    features['Forward Byte Mean'] = df['Fwd Packet Length Mean']
    features['Forward Byte Std'] = df['Fwd Packet Length Std']
    features['Forward Byte Variance'] = (((features['Forward Byte Max'] - features['Forward Byte Mean']) ** 2) + ((features['Forward Byte Mean'] - features['Forward Byte Min']) ** 2)) / 2

    features['Backward Packets'] = bwd
    features['Backward Bytes'] = df['Bwd Packet Length Mean'] * bwd
    features['Backward Packet Rate'] = bwd / (duration + 1e-6)
    features['Backward Byte Rate'] = (df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6)
    features['Backward Byte Max'] = df['Bwd Packet Length Max']
    features['Backward Byte Min'] = df['Bwd Packet Length Min']
    features['Backward Byte Mean'] = df['Bwd Packet Length Mean']
    features['Backward Byte Std'] = df['Bwd Packet Length Std']
    features['Backward Byte Variance'] = (((features['Backward Byte Max'] - features['Backward Byte Mean']) ** 2) + ((features['Backward Byte Mean'] - features['Backward Byte Min']) ** 2)) / 2


    features['Total IAT'] = df['Fwd IAT Total'] + df['Bwd IAT Total']
    features['Total IAT Max'] = df[['Fwd IAT Max', 'Bwd IAT Max']].max(axis=1)
    features['Total IAT Min'] = df[['Fwd IAT Min', 'Bwd IAT Min']].min(axis=1)
    features['Total IAT Mean'] = (df['Fwd IAT Total'] + df['Bwd IAT Total']) / (fwd + bwd + 1e-6)
    features['Total IAT Std'] = df['Flow IAT Std']
    features['Total IAT Variance'] = (((features['Total IAT Max'] - features['Total IAT Mean']) ** 2) + ((features['Total IAT Mean'] - features['Total IAT Min']) ** 2)) / 2
    features['Forward IAT'] = df['Fwd IAT Total']
    features['Forward IAT Max'] = df['Fwd IAT Max']
    features['Forward IAT Min'] = df['Fwd IAT Min']
    features['Forward IAT Mean'] = df['Fwd IAT Total'] / (fwd + 1e-6)
    features['Forward IAT Std'] = df['Fwd IAT Std']
    features['Forward IAT Variance'] = (((features['Forward IAT Max'] - features['Forward IAT Mean']) ** 2) + ((features['Forward IAT Mean'] - features['Forward IAT Min']) ** 2)) / 2
    features['Backward IAT'] = df['Bwd IAT Total']
    features['Backward IAT Max'] = df['Bwd IAT Max']
    features['Backward IAT Min'] = df['Bwd IAT Min']
    features['Backward IAT Mean'] = df['Bwd IAT Total'] / (bwd + 1e-6)
    features['Backward IAT Std'] = df['Bwd IAT Std']
    features['Backward IAT Variance'] = (((features['Backward IAT Max'] - features['Backward IAT Mean']) ** 2) + ((features['Backward IAT Mean'] - features['Backward IAT Min']) ** 2)) / 2

    features['Active Max'] = df['Active Max']
    features['Active Min'] = df['Active Min']
    features['Active Mean'] = df['Active Mean']
    features['Active Std'] = df['Active Std']
    features['Active Variance'] = (((features['Active Max'] - features['Active Mean']) ** 2) + ((features['Active Mean'] - features['Active Min']) ** 2)) / 2
    features['Idle Max'] = df['Idle Max']
    features['Idle Min'] = df['Idle Min']
    features['Idle Mean'] = df['Idle Mean']
    features['Idle Std'] = df['Idle Std']
    features['Idle Variance'] = (((features['Idle Max'] - features['Idle Mean']) ** 2) + ((features['Idle Mean'] - features['Idle Min']) ** 2)) / 2

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
    # features['Failed Connection'] = 1 if ((features['proto_'] == 6) and (syn > 0) and (ack == 0)) else 0

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)
    features = features.clip(-1e6, 1e6)
    features = features.astype(np.float32)

    if save_type == 'export':
        if 'Label' in df.columns:
            labels = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)
            labels.to_csv(f'../datasets/processed/rf_labels_{label}.csv', index=False)

        features.to_csv(f'../datasets/processed/rf_{label}.csv', index=False)
        return None

    return features


def extract_features_ae(df, label="", save_type=None):
    df.columns = df.columns.str.strip()
    features = pd.DataFrame()

    fwd = df['Total Fwd Packets']
    bwd = df['Total Backward Packets']
    duration = df['Flow Duration']

    features['Duration'] = np.log1p(duration / 1_000_000)
    features['In/Out Ratio'] = np.log1p(fwd) - np.log1p(bwd)
    features['Absolute Difference'] = abs(fwd - bwd) / (fwd + bwd + 1e-6)
    features['Byte Rate Asymmetry'] = abs(np.log1p((df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6)) - np.log1p((df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6)))
    features['Active/Idle Ratio'] = abs(df['Active Mean'] - df['Idle Mean'])/(df['Active Mean'] + df['Idle Mean'] + 1e-6)

    features['Forward Packet Rate'] = np.log1p(fwd / (duration + 1e-6))
    features['Forward Byte Rate'] = np.log1p((df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6))
    features['Forward Byte Mean'] = df['Fwd Packet Length Mean']
    features['Forward Byte Std'] = df['Fwd Packet Length Std']

    features['Backward Packet Rate'] = np.log1p(bwd / (duration + 1e-6))
    features['Backward Byte Rate'] = np.log1p((df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6))
    features['Backward Byte Mean'] = df['Bwd Packet Length Mean']
    features['Backward Byte Std'] = df['Bwd Packet Length Std']

    features['Forward IAT Mean'] = np.log1p(df['Fwd IAT Total'] / (fwd + 1e-6))
    features['Forward IAT Std'] = df['Fwd IAT Std']
    features['Backward IAT Mean'] = np.log1p(df['Bwd IAT Total'] / (bwd + 1e-6))
    features['Backward IAT Std'] = df['Bwd IAT Std']

    features['Active Mean'] = df['Active Mean']
    features['Active Std'] = df['Active Std']
    features['Idle Mean'] = df['Idle Mean']
    features['Idle Std'] = df['Idle Std']
    # features['Failed Connection'] = 1 if ((features['proto_'] == 6) and (syn > 0) and (ack == 0)) else 0

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)
    features = features.clip(-1e6, 1e6)
    features = features.astype(np.float32)

    if save_type == 'export':
        features.to_csv(f'../datasets/processed/ae_{label}.csv', index=False)
        return None

    return features

def process_raw_dataset():
    df = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_ae_training.csv', low_memory=False)
    extract_features_ae(df, 'training', save_type='export')

    df = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_ae_testing_benign.csv', low_memory=False)
    extract_features_ae(df, 'testing_benign', save_type='export')

    df = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_ae_testing_malicious.csv', low_memory=False)
    extract_features_ae(df, 'testing_malicious', save_type='export')

    df = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_rf_training.csv', low_memory=False)
    extract_features_rf(df, 'training', save_type='export')

    df = pd.read_csv('../datasets/raw/CICIDS2017/Aggregated/CICIDS2017_rf_testing.csv', low_memory=False)
    extract_features_rf(df, 'testing', save_type='export')
