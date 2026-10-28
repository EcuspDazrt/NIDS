import argparse, signal, sys, winreg
import util.paths as p

from multiprocessing import Process, Queue, Event
from capture.capture import capture_process
from inference.inference import inference_process
from gui.create_dashboard import create_tray_icon
from alerts.alert_engine import AlertEngine
from util.logger import get_logger
LOGGER = get_logger(__name__)

# Crucial thresholds and parameters. Check retraining.py for more
RF_THRESHOLD = 2
AE_THRESHOLD = 2
DEFENSES = {'Isolation Forest':True, 'Temporal Isolation':True, 'Rollback':True}
INTERVALS = [7200, 86400, 172800] # drift check interval, retrain interval, drift cooldown - currently 2 hours, 1 day, and 2 days respectively

def register_app_id():
    if sys.platform == 'win32':
        try:
            key_path = r'SOFTWARE\Classes\AppUserModelId\NIDS.NetworkIntrusionDetection'
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, 'DisplayName', 0, winreg.REG_SZ, 'NIDS')
                winreg.SetValueEx(key, 'IconUri', 0, winreg.REG_SZ,
                                  str(p.ICON_PATH))
        except Exception:
            LOGGER.exception(f'Could not register app ID')

def init_app_user():
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            LOGGER.warning('Error setting up user process (Windows only)')
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                LOGGER.exception('Could not set up user process (Windows only)')
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('NIDS.NetworkIntrusionDetection')

# dependency refactoring (use the functions in util/paths.py)
# hook up the logging so it's easy to know what's going on in the system
# implement centralized feature retrieval from datasets
# mass refactoring of retraining system for readability and efficiency

if __name__ == "__main__":
    init_app_user()
    register_app_id()

    parser = argparse.ArgumentParser(description='NIDS - Network Intrusion Detection System')
    parser.add_argument('--interface', '-i', type=str, required=False, help='Network interface to monitor (e.g. eth0, en0, or Windows NPF device GUID)')
    parser.add_argument('--pcap-file', '-p', type=str, required=False, help='Pcap file to monitor')

    args = parser.parse_args()
    interface = args.interface
    if interface:
        interface = interface.replace('Tcpip', 'NPF')
    pcap_file = args.pcap_file
    if not pcap_file and not interface:
        pcap_file = p.DATASETS_DIR / 'pcaps' / 'FIRST-2015_Hands-on_Network_Forensics_PCAP' / '2015-03-05' / 'snort.log.1425565276'

    if pcap_file and interface:
        raise(Exception('Only one of interface or pcap-file can be specified'))
    if not pcap_file and not interface:
        raise(Exception('Interface or pcap-file need to be specified'))

    flow_queue = Queue()
    results_queue = Queue(maxsize=500)
    stop_capture = Event()
    models_ready = Event()
    flash_event = Event()

    alert_engine = AlertEngine(RF_THRESHOLD, AE_THRESHOLD, results_queue, flash_event)

    if interface:
        capture = Process(target=capture_process, args=(flow_queue, stop_capture, 'live-capture', interface))
    else:
        capture = Process(target=capture_process, args=(flow_queue, stop_capture, 'simulation', None, pcap_file))

    inference = Process(target=inference_process, args=(flow_queue, results_queue, models_ready, alert_engine))

    capture.daemon = True
    inference.daemon = True

    capture.start()
    inference.start()

    def shutdown(sig, frame):
        stop_capture.set()
        capture.terminate()
        inference.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    create_tray_icon(results_queue, stop_capture, models_ready, alert_engine, flash_event, DEFENSES, INTERVALS)