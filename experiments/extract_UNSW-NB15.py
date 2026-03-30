from capture.capture import capture_process
from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
from multiprocessing import Event, Queue
import threading
import pandas as pd

from pathlib import Path
BASE_DIR = Path(__file__).parent

flow_queue = Queue()
stop_capture = Event()

base_pcap_dir = BASE_DIR.parent / 'datasets' / 'raw' / 'pcaps' / 'FIRST-2015_Hands-on_Network_Forensics_PCAP'
# pcap_dirs = ['pcaps 17-2-2015', 'pcaps 22-1-2015']
pcap_dirs = ['2015-03-05', '2015-03-06']

class LastFlow:
    def __init__(self):
        self.last_flow_got = None
    def set(self, last_flow_got):
        self.last_flow_got = last_flow_got
    def get(self):
        return self.last_flow_got

def extract_features(ae_rows, rf_rows):
    while True:
        flow = flow_queue.get()
        if flow is None:
            break
        ae_rows.append(extract_ae(flow))
        rf_rows.append(extract_rf(flow))

ae_rows = []
rf_rows = []

extract = threading.Thread(target=extract_features, args=(ae_rows, rf_rows))
extract.start()

for pcap_dir in base_pcap_dir.glob('*'):
    for pcap_path in (base_pcap_dir / pcap_dir).glob('*'):
        print('Processing', pcap_path)
        capture = threading.Thread(target=capture_process, args=(flow_queue, stop_capture, 'simulation', None, str(pcap_path).encode()))
        capture.start()
        capture.join()

flow_queue.put(None)
extract.join()

final_ae = pd.DataFrame(ae_rows)
final_rf = pd.DataFrame(rf_rows)
final_ae.to_csv('final_ae_features.csv')
final_rf.to_csv('final_rf_features.csv')
print(f'Saved {len(ae_rows)} ae flows and {len(rf_rows)} rf flows')
