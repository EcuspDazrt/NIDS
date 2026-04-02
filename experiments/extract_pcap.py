# extracts ae and rf features from a pcap file and exports it to a csv for future use
from capture.capture import capture_process
from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
from multiprocessing import Event, Queue
import threading
import pandas as pd

from pathlib import Path
BASE_DIR = Path(__file__).parent
base_pcap_dir = BASE_DIR.parent / 'datasets' / 'raw' / 'pcaps'

flow_queue = Queue()
stop_capture = Event()

def extract_pcap(dir_name, save_rf=False, label='baseline'):
    dir_name = Path(base_pcap_dir / dir_name)
    if not dir_name.exists():
        return

    def extract_features(ae_rows, rf_rows, save_rf=False):
        while True:
            flow = flow_queue.get()
            if flow is None:
                break
            ae_rows.append(extract_ae(flow))

            if save_rf:
                rf_rows.append(extract_rf(flow))

    ae_rows = []
    rf_rows = []

    extract = threading.Thread(target=extract_features, args=(ae_rows, rf_rows, save_rf))
    extract.start()

    for pcap_dir in dir_name.glob('*'):
        for pcap_path in (dir_name / pcap_dir).glob('*'):
            print('Processing', pcap_path)
            capture = threading.Thread(target=capture_process, args=(flow_queue, stop_capture, 'simulation', None, str(pcap_path).encode()))
            capture.start()
            capture.join()

    flow_queue.put(None)
    extract.join()

    final_ae = pd.DataFrame(ae_rows)
    final_ae.to_csv('final_ae_features.csv')

    if save_rf:
        final_rf = pd.DataFrame(rf_rows)
        final_rf.to_csv('final_rf_features.csv')

    print(f'Saved {len(ae_rows)} ae flows and {len(rf_rows)} rf flows')

if __name__ == '__main__':
    extract_pcap(dir='FIRST-2015_Hands-on_Network_Forensics_PCAP', save_rf=True)