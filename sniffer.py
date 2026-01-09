import pandas as pd

fpath = 'datasets/GeneratedLabelledFlows/TrafficLabelling/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'

df = pd.read_csv(fpath)

# print(df.columns)

features = df.drop(columns=['Protocol', 'Flow Duration'])
print(features)