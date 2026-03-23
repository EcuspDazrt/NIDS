import argparse
import signal
import sys
if sys.platform == 'win32':
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('NIDS.NetworkIntrusionDetection')

from multiprocessing import Process, Queue, Event
from capture.capture import capture_process
from inference.inference import inference_process
from gui.create_dashboard import create_tray_icon
from alerts.alert_engine import AlertEngine

RF_THRESHOLD = 2
AE_THRESHOLD = 2

def register_app_id():
    if sys.platform == 'win32':
        try:
            import winreg
            from pathlib import Path
            key_path = r'SOFTWARE\Classes\AppUserModelId\NIDS.NetworkIntrusionDetection'
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, 'DisplayName', 0, winreg.REG_SZ, 'NIDS')
                winreg.SetValueEx(key, 'IconUri', 0, winreg.REG_SZ,
                                  str(Path(__file__).parent / 'gui' / 'resources' / 'nids_logo.png'))
        except Exception as e:
            print(f'Could not register app ID: {e}')

if __name__ == "__main__":
    register_app_id()

    parser = argparse.ArgumentParser(description='NIDS - Network Intrusion Detection System')
    parser.add_argument('--interface', '-i', type=str, required=True, help='Network interface to monitor (e.g. eth0, en0, or Windows NPF device GUID)')
    args = parser.parse_args()
    interface = args.interface.replace('Tcpip', 'NPF')

    flow_queue = Queue()
    results_queue = Queue(maxsize=500)
    stop_capture = Event()
    models_ready = Event()
    flash_event = Event()

    alert_engine = AlertEngine(RF_THRESHOLD, AE_THRESHOLD, results_queue, flash_event)

    capture = Process(target=capture_process, args=(flow_queue, stop_capture, 'live_capture', interface))
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

    create_tray_icon(results_queue, stop_capture, models_ready, alert_engine, flash_event)