# logs live traffic (to be used on a virtual machine) and exports it to a .pcap file
import subprocess
import time
from pathlib import Path
from datetime import datetime

def log_pcap(interface='eth0', duration=60, output_dir='captures', label='baseline'):
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'{output_dir}/{label}_{timestamp}.pcap'

    cmd = ['sudo', 'tcpdump', '-i', interface, '-w', output_path]
    process = subprocess.Popen(cmd)

    print(f'Capturing to {output_path} for {duration} seconds...')
    time.sleep(duration)
    process.terminate()
    process.wait()

    print(f'Capture complete: {output_path}')
    return output_path