# logs live traffic (to be used on a virtual machine) and exports it to a .pcap file
import subprocess
import threading
from multiprocessing import Queue, Event
from pathlib import Path
from datetime import datetime
from capture.capture import capture_process


def start_capture(interface, output_path, flow_queue, stop_capture, label, target_flows):
    tcpdump = subprocess.Popen(['sudo', 'tcpdump', '-i', interface, '-w', str(output_path)], stderr=subprocess.DEVNULL)
    cap_thread = threading.Thread(target=capture_process, args=(flow_queue, stop_capture, 'live-capture', interface, None), daemon=True)
    cap_thread.start()

    print(f'[{label}] Capturing to {output_path.name}, target: {target_flows} flows...')

    return tcpdump, cap_thread


def shutdown_capture(stop_capture, cap_thread, tcpdump):
    stop_capture.set()
    cap_thread.join(timeout=10)
    tcpdump.terminate()
    tcpdump.wait()


def process_capture(target_flows, flow_queue, label, output_path):
    flow_count = 0
    while flow_count < target_flows:
        try:
            flow = flow_queue.get(timeout=180)
        except Exception:
            print(f'\tWarning: no flows received in 3 minutes - interface may be idle | {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')
            continue

        if flow is None:
            print('\tCapture process ended unexpectedly')
            break

        flow_count += 1
        if flow_count % max(1, target_flows // 10) == 0:
            print(f'\t{flow_count}/{target_flows} flows')

    print(f'[{label}] Done - {flow_count} flows captured -> {output_path}')
    return flow_count


def log_pcap(output_dir: Path, interface=b'eth0', target_flows=5000, label='*'):
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'{label}_{timestamp}.pcap'

    stop_capture = Event()
    flow_queue = Queue()

    tcpdump, cap_thread = start_capture(interface, output_path, flow_queue, stop_capture, label, target_flows)
    flow_count = process_capture(target_flows, flow_queue, label, output_path)
    shutdown_capture(stop_capture, cap_thread, tcpdump)

    return str(output_path), flow_count
