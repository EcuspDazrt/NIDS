import pandas as pd
import numpy as np
import util.paths as p

from util.logger import get_logger
LOGGER = get_logger(__name__)

def is_private(ip_series):
    return (
        ip_series.str.startswith('10.') |
        ip_series.str.startswith('192.168.') |
        ip_series.str.match(r'^172\.(1[6-9]|2\d|3[01])\.') |
        ip_series.str.startswith('127.')
    ).astype(int)

def port_category(port_series):
    import pandas as pd
    import numpy as np

    # Handle scalar input during inference
    if np.isscalar(port_series):
        port = port_series if port_series is not None else 0
        if port <= 1023:
            return 0
        elif port <= 49151:
            return 1
        else:
            return 2

    # Original Series path for training
    return pd.cut(
        port_series.fillna(0),
        bins=[-1, 1023, 49151, float('inf')],
        labels=[0, 1, 2]
    ).astype(int)

def extract_features_rf(df, label="", save_type=None, experiment=False):
    df.columns = df.columns.str.strip()

    d = df[(df['Total Fwd Packets'] == 2) & (df['Fwd Packet Length Max'] > df['Fwd Packet Length Min'])]
    # print((d['Fwd Packet Length Std'] / (d['Fwd Packet Length Max'] - d['Fwd Packet Length Min'])).describe())

    # df = df.dropna(how='all')  # drop rows where every column is null
    # df = df.dropna(subset=['Destination Port', 'Flow Duration', 'Protocol'])  # drop rows missing critical fields

    null_counts = df.isnull().sum()
    if null_counts.any():
        LOGGER.warning(f"Null values in source data:\n{null_counts[null_counts > 0]}")

    features = pd.DataFrame()

    fwd = df['Total Fwd Packets']
    bwd = df['Total Backward Packets']
    syn = df['SYN Flag Count']
    ack = df['ACK Flag Count']
    fin = df['FIN Flag Count']
    rst = df['RST Flag Count']
    duration = df['Flow Duration'] / 1_000_000

    all_protocols = [0, 6, 17]
    if 'Protocol' not in df.columns:
        flag_cols = ['SYN Flag Count', 'ACK Flag Count', 'FIN Flag Count', 'RST Flag Count']
        df['Protocol'] = np.where(df[flag_cols].any(axis=1), 6, 17)

    df['Protocol'] = pd.to_numeric(df['Protocol'], errors='coerce').fillna(0).astype(int)
    df['Protocol'] = pd.Categorical(df['Protocol'], categories=all_protocols)
    proto_onehot = pd.get_dummies(df['Protocol'], prefix='proto', dtype=int)
    features = pd.concat([features, proto_onehot], axis=1)

    features['Port'] = port_category(df['Destination Port'])
    features['IP'] = is_private(df['Destination IP'])
    features['Duration'] = duration
    features['In/Out Ratio'] = fwd / (bwd + 1e-6)

    features['Total Packets'] = fwd + bwd
    features['Total Bytes'] = (df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)
    features['Total Packet Rate'] = (fwd + bwd) / (duration + 1e-6)
    features['Total Byte Rate'] = ((df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)) / (duration + 1e-6)
    features['Total Byte Max'] = df[['Fwd Packet Length Max', 'Bwd Packet Length Max']].max(axis=1)
    features['Total Byte Min'] = df[['Fwd Packet Length Min', 'Bwd Packet Length Min']].min(axis=1)
    features['Total Byte Mean'] = ((df['Fwd Packet Length Mean'] * fwd) + (df['Bwd Packet Length Mean'] * bwd)) / (fwd + bwd + 1e-6)
    features['Total Byte Std'] = df['Packet Length Std']
    features['Total Byte Variance'] = df['Packet Length Std'] ** 2

    features['Forward Packets'] = fwd
    features['Forward Bytes'] = df['Fwd Packet Length Mean'] * fwd
    features['Forward Packet Rate'] = fwd / (duration + 1e-6)
    features['Forward Byte Rate'] = (df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6)
    features['Forward Byte Max'] = df['Fwd Packet Length Max']
    features['Forward Byte Min'] = df['Fwd Packet Length Min']
    features['Forward Byte Mean'] = df['Fwd Packet Length Mean']
    features['Forward Byte Std'] = df['Fwd Packet Length Std']
    features['Forward Byte Variance'] = df['Fwd Packet Length Std'] ** 2

    features['Backward Packets'] = bwd
    features['Backward Bytes'] = df['Bwd Packet Length Mean'] * bwd
    features['Backward Packet Rate'] = bwd / (duration + 1e-6)
    features['Backward Byte Rate'] = (df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6)
    features['Backward Byte Max'] = df['Bwd Packet Length Max']
    features['Backward Byte Min'] = df['Bwd Packet Length Min']
    features['Backward Byte Mean'] = df['Bwd Packet Length Mean']
    features['Backward Byte Std'] = df['Bwd Packet Length Std']
    features['Backward Byte Variance'] = df['Bwd Packet Length Std'] ** 2


    features['Total IAT'] = (df['Fwd IAT Total'] + df['Bwd IAT Total']) / 1_000_000
    features['Total IAT Max'] = (df[['Fwd IAT Max', 'Bwd IAT Max']].max(axis=1)) / 1_000_000
    features['Total IAT Min'] = (df[['Fwd IAT Min', 'Bwd IAT Min']].min(axis=1)) / 1_000_000
    features['Total IAT Mean'] = ((df['Fwd IAT Total'] + df['Bwd IAT Total']) / (fwd + bwd + 1e-6)) / 1_000_000
    features['Total IAT Std'] = (df['Flow IAT Std']) / 1_000_000
    features['Total IAT Variance'] = (df['Flow IAT Std'] / 1_000_000) ** 2
    features['Forward IAT'] = (df['Fwd IAT Total']) / 1_000_000
    features['Forward IAT Max'] = (df['Fwd IAT Max']) / 1_000_000
    features['Forward IAT Min'] = (df['Fwd IAT Min']) / 1_000_000
    features['Forward IAT Mean'] = (df['Fwd IAT Total'] / (fwd + 1e-6)) / 1_000_000
    features['Forward IAT Std'] = (df['Fwd IAT Std']) / 1_000_000
    features['Forward IAT Variance'] = (df['Fwd IAT Std'] / 1_000_000) ** 2
    features['Backward IAT'] = (df['Bwd IAT Total']) / 1_000_000
    features['Backward IAT Max'] = (df['Bwd IAT Max']) / 1_000_000
    features['Backward IAT Min'] = (df['Bwd IAT Min']) / 1_000_000
    features['Backward IAT Mean'] = (df['Bwd IAT Total'] / (bwd + 1e-6)) / 1_000_000
    features['Backward IAT Std'] = (df['Bwd IAT Std']) / 1_000_000
    features['Backward IAT Variance'] = (df['Bwd IAT Std'] / 1_000_000) ** 2

    features['Active Max'] = (df['Active Max']) / 1_000_000
    features['Active Min'] = (df['Active Min']) / 1_000_000
    features['Active Mean'] = (df['Active Mean']) / 1_000_000
    features['Active Std'] = (df['Active Std']) / 1_000_000
    features['Active Variance'] = (df['Active Std'] / 1_000_000) ** 2
    features['Idle Max'] = (df['Idle Max']) / 1_000_000
    features['Idle Min'] = (df['Idle Min']) / 1_000_000
    features['Idle Mean'] = (df['Idle Mean']) / 1_000_000
    features['Idle Std'] = (df['Idle Std']) / 1_000_000
    features['Idle Variance'] = (df['Idle Std'] / 1_000_000) ** 2

    features['Syn Ratio'] = syn / (fwd + bwd + 1e-6)
    features['Ack Ratio'] = ack / (fwd + bwd + 1e-6)
    features['Fin Ratio'] = fin / (fwd + bwd + 1e-6)
    features['Rst Ratio'] = rst / (fwd + bwd + 1e-6)
    features['Syn Rate'] = syn / (duration + 1e-6)
    features['Ack Rate'] = ack / (duration + 1e-6)
    features['Fin Rate'] = fin / (duration + 1e-6)
    features['Rst Rate'] = rst / (duration + 1e-6)
    features['Syn/Ack Ratio'] = syn / (ack + 1e-6)
    features['Fin/Ack Ratio'] = fin / (ack + 1e-6)
    features['Rst/Syn Ratio'] = rst / (syn + 1e-6)

    rate_cols = [
        'Total Packet Rate', 'Total Byte Rate',
        'Forward Packet Rate', 'Forward Byte Rate',
        'Backward Packet Rate', 'Backward Byte Rate',
        'Syn Rate', 'Ack Rate', 'Fin Rate', 'Rst Rate'
    ]

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)
    features = features.clip(-1e6, 1e6)
    features = features.astype(np.float32)

    if experiment:
        features['Label'] = df['Label']

    if save_type == 'export':
        if 'Label' in df.columns:
            binary_labels = (df['Label'] != 'BENIGN').astype(int)
            binary_labels.to_csv(p.DATASETS_DIR/'processed'/f'rf_labels_{label}.csv', index=False)

            df['Label'].to_csv(p.DATASETS_DIR/'processed'/f'rf_categories_{label}.csv', index=False)

        features.to_csv(p.DATASETS_DIR/'processed'/f'rf_{label}.csv', index=False)
        return None

    return features


def extract_features_ae(df, label="", save_type=None, experiment=False):
    df.columns = df.columns.str.strip()

    # df = df.dropna(how='all')  # drop rows where every column is null
    # df = df.dropna(subset=['Destination Port', 'Flow Duration', 'Protocol'])  # drop rows missing critical fields

    null_counts = df.isnull().sum()
    if null_counts.any():
        LOGGER.warning(f'Null values in source data:\n{null_counts[null_counts > 0]}')

    features = pd.DataFrame()

    fwd = df['Total Fwd Packets']
    bwd = df['Total Backward Packets']
    duration = df['Flow Duration'].clip(lower=0) / 1_000_000

    features['Duration'] = np.log1p(duration)
    features['In/Out Ratio'] = np.log1p(fwd) - np.log1p(bwd)
    features['Absolute Difference'] = abs(fwd - bwd) / (fwd + bwd + 1e-6)
    features['Byte Rate Asymmetry'] = abs(np.log1p((df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6)) - np.log1p((df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6)))

    features['Forward Packet Rate'] = np.log1p(fwd / (duration + 1e-6))
    features['Forward Byte Rate'] = np.log1p((df['Fwd Packet Length Mean'] * fwd) / (duration + 1e-6))
    features['Forward Byte Mean'] = np.log1p(df['Fwd Packet Length Mean'])
    features['Forward Byte Std'] = np.log1p(df['Fwd Packet Length Std'])

    features['Backward Packet Rate'] = np.log1p(bwd / (duration + 1e-6))
    features['Backward Byte Rate'] = np.log1p((df['Bwd Packet Length Mean'] * bwd) / (duration + 1e-6))
    features['Backward Byte Mean'] = np.log1p(df['Bwd Packet Length Mean'])
    features['Backward Byte Std'] = np.log1p(df['Bwd Packet Length Std'])

    features['Forward IAT Mean'] = np.log1p((df['Fwd IAT Total'] / (fwd + 1e-6)) / 1_000_000)
    features['Forward IAT Std'] = np.log1p((df['Fwd IAT Std']) / 1_000_000)
    features['Backward IAT Mean'] = np.log1p((df['Bwd IAT Total'] / (bwd + 1e-6)) / 1_000_000)
    features['Backward IAT Std'] = np.log1p((df['Bwd IAT Std']) / 1_000_000)

    features['Active Mean'] = np.log1p((df['Active Mean']) / 1_000_000)
    features['Active Std'] = np.log1p((df['Active Std']) / 1_000_000)
    features['Idle Mean'] = np.log1p((df['Idle Mean']) / 1_000_000)
    features['Idle Std'] = np.log1p((df['Idle Std']) / 1_000_000)

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)
    features = features.clip(-1e6, 1e6)
    features = features.astype(np.float32)

    if experiment:
        features['Label'] = df['Label']

    if save_type == 'export':
        features.to_csv(p.DATASETS_DIR/'processed'/f'ae_{label}.csv', index=False)
        return None

    return features

def process_raw_dataset():
    LOGGER.info('Dataset started processing')
    if not p.raw_dataset_exists():
        return

    df = pd.read_csv(p.RAW_AE_TRAIN_PATH, low_memory=False)
    extract_features_ae(df, 'training', save_type='export')

    df = pd.read_csv(p.RAW_AE_TEST_BENIGN_PATH, low_memory=False)
    extract_features_ae(df, 'testing_benign', save_type='export')

    df = pd.read_csv(p.RAW_AE_TEST_MALICIOUS_PATH, low_memory=False)
    extract_features_ae(df, 'testing_malicious', save_type='export')

    df = pd.read_csv(p.RAW_RF_TRAIN_PATH, low_memory=False)
    extract_features_rf(df, 'training', save_type='export')

    df = pd.read_csv(p.RAW_RF_TEST_PATH, low_memory=False)
    extract_features_rf(df, 'testing', save_type='export')

    LOGGER.info('Dataset finished processing')

if __name__ == '__main__':
    process_raw_dataset()