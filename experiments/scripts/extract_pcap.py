# extracts ae and rf features from a pcap file and exports it to a csv for future use
from capture.capture import capture_process
from features.extract_inference import extract_features_ae as extract_ae, extract_features_rf as extract_rf
from experiments.scripts.database_handler import log_flow, init_experimental_db as init_db

from multiprocessing import Event, Queue
import threading
import pandas as pd
import experiments.scripts.paths as p


def extract_features(ae_rows, rf_rows, db_path, flow_queue, save_rf=False):
    if db_path is not None:
        init_db(db_path)

    while True:
        flow = flow_queue.get()
        if flow is None:
            break

        ae_row = extract_ae(flow, experiment=True)
        ae_rows.append(ae_row)
        rf_row = None
        if save_rf:
            rf_row = extract_rf(flow, experiment=True)
            rf_rows.append(rf_row)

        if db_path is not None:
            log_flow(db_path, ae_features_dict=ae_row, rf_features_dict=rf_row)


def extract_pcap(csv_save_dir, pcap_path, save_rf=False, label='*', db_path=None):
    flow_queue = Queue()
    stop_capture = Event()

    ae_rows = []
    rf_rows = []

    extract = threading.Thread(target=extract_features, args=(ae_rows, rf_rows, db_path, flow_queue, save_rf))
    extract.start()

    if pcap_path.is_dir():
        pcap_files = [pth for pth in pcap_path.glob('**/*') if pth.suffix == '.pcap' or '.log' in pth.name]
    else:
        pcap_files = [pcap_path]

    for path in pcap_files:
        print('Processing', path)
        capture = threading.Thread(target=capture_process, args=(flow_queue, stop_capture, 'simulation', None, str(path).encode()))
        capture.start()
        capture.join()

    flow_queue.put(None)
    extract.join()

    final_ae = pd.DataFrame(ae_rows)
    final_ae.to_csv(csv_save_dir / f'ae_{label}.csv')

    if save_rf:
        final_rf = pd.DataFrame(rf_rows)
        final_rf.to_csv(csv_save_dir / f'rf_{label}.csv')
        print(f'Saved {len(ae_rows)} ae flows and {len(rf_rows)} rf flows')
        return

    print(f'Saved {len(ae_rows)} ae flows')
    return


if __name__ == '__main__':
    extract_pcap(r"UNSW-NB15\17-2-2015\27.pcap", save_rf=True, label='test')
