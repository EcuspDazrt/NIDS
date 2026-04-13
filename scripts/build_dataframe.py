from pathlib import Path
import pandas as pd

# initialize training and eval raw datasets
BASE_DIR = Path(__file__).parent
all_paths = [BASE_DIR.parent/'datasets'/'CICIDS2017'/'Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Friday-WorkingHours-Morning.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Tuesday-WorkingHours.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Wednesday-workingHours.pcap_ISCX.csv',
             BASE_DIR.parent/'datasets'/'CICIDS2017'/'Monday-WorkingHours.pcap_ISCX.csv']

def drop(df, handle_benign):
    df.columns = df.columns.str.strip()
    if handle_benign == 'DROP':
        df = df[df['Label'] != 'BENIGN']
        df = df.drop('Label', axis=1)
    if handle_benign == 'KEEP':
        df = df[df['Label'] == 'BENIGN']
        df = df.drop('Label', axis=1)
    return df.drop(columns=['Total Length of Fwd Packets', 'Total Length of Bwd Packets',
                            'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Max',
                            'Flow IAT Min', 'Fwd PSH Flags',
                            'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
                            'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s',
                            'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
                            'Packet Length Mean', 'Packet Length Variance',
                            'PSH Flag Count', 'URG Flag Count',
                            'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
                            'Average Packet Size', 'Avg Fwd Segment Size',
                            'Avg Bwd Segment Size', 'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk',
                            'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
                            'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Subflow Fwd Packets',
                            'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
                            'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
                            'act_data_pkt_fwd', 'min_seg_size_forward',
                            'Fwd IAT Mean', 'Bwd IAT Mean'])

    # Not in kaggle dataset:
    # 'Flow ID', 'Source IP', 'Source Port', 'Timestamp',

    # Data that remains:

    # 'Flow Duration', 'Protocol', 'Destination Port', 'Destination IP',
    # 'Total Fwd Packets', 'Total Backward Packets',
    # 'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
    # 'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
    # 'Fwd Packet Length Std', 'Bwd Packet Length Std',
    # 'Fwd IAT Min', 'Fwd IAT Max', 'Fwd IAT Total',
    # 'Bwd IAT Min', 'Bwd IAT Max', 'Bwd IAT Total',
    # 'Fwd IAT Std', 'Bwd IAT Std'
    # 'Active Max', 'Active Min', 'Active Mean',
    # 'Idle Max', 'Idle Min', 'Idle Mean',
    # 'Active Std', 'Idle Std',
    # 'SYN Flag Count', 'ACK Flag Count',
    # 'FIN Flag Count', 'RST Flag Count',
    # 'Flow IAT Std', 'Packet Length Std'

def create_dataframe(paths, label, handle_benign=None):
    df = pd.DataFrame()

    for path in paths:
        df = pd.concat([df, drop(pd.read_csv(path, encoding='latin1', low_memory=False), handle_benign=handle_benign)], ignore_index=True)

    df.to_csv(BASE_DIR.parent/'datasets'/'raw'/'Aggregated'/f'CICIDS2017_{label}.csv', index=False)

def init_dataframes():
    print('Initializing dataframes...')

    if not Path(BASE_DIR.parent/'datasets'/'raw'/'Aggregated').exists():
        import os
        os.mkdir(BASE_DIR.parent/'datasets'/'raw'/'Aggregated')

    all_df = pd.DataFrame()
    for path in all_paths:
        df = pd.read_csv(path, encoding='latin1', low_memory=False)
        df.columns = df.columns.str.strip()
        all_df = pd.concat([all_df, df], ignore_index=True)
        all_df = all_df.dropna(subset=['Label'])

    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(
        all_df,
        test_size=0.3,
        stratify=all_df['Label'],
        random_state=42)

    train_df[train_df['Label'] == 'BENIGN'].drop('Label', axis=1).to_csv(BASE_DIR.parent / 'datasets' / 'raw' / 'Aggregated/CICIDS2017_ae_training.csv', index=False)
    test_df[test_df['Label'] == 'BENIGN'].drop('Label', axis=1).to_csv(BASE_DIR.parent / 'datasets' / 'raw' / 'Aggregated/CICIDS2017_ae_testing_benign.csv', index=False)
    test_df[test_df['Label'] != 'BENIGN'].drop('Label', axis=1).to_csv(BASE_DIR.parent / 'datasets' / 'raw' / 'Aggregated/CICIDS2017_ae_testing_malicious.csv',index=False)
    train_df.to_csv(BASE_DIR.parent / 'datasets' / 'raw' / 'Aggregated/CICIDS2017_rf_training.csv', index=False)
    test_df.to_csv(BASE_DIR.parent / 'datasets' / 'raw' / 'Aggregated/CICIDS2017_rf_testing.csv', index=False)

if __name__ == '__main__':
    init_dataframes()
