import joblib

from training_features import extract_features_training as extract, create_dataframe as create_df
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from pathlib import Path

import pandas as pd
import joblib as jb


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

THRESHOLD = 0.03

def train_model():
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=20,
        class_weight='balanced_subsample',
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(x_train, y_train)

    print('Saving model...\n')
    jb.dump(rf, 'rf_model.pkl')

# print('Creating testing database\n')
# create_df(paths_testing, 'testing')
# print('Finished creating testing database\n')

# print('Creating training database\n')
# create_df(paths_training, 'training')
# print('Finished creating training database\n')

print('\nReading training data and extracting features...\n')
x_train, y_train = extract(pd.read_csv('CICIDS2017_training.csv', low_memory=False))

print('Loading model...\n')
rf = jb.load('rf_model.pkl')

# print('Training model...\n')
# train_model()

print('Reading testing data and extracting features...\n')
x_test, y_test = extract(pd.read_csv('CICIDS2017_testing.csv', low_memory=False))

print('Running testing...\n')
proba = rf.predict_proba(x_test)[:,1]
y_pred = (proba > THRESHOLD).astype(int)
print('Finished testing')

print(classification_report(y_test, y_pred))