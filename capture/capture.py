import ctypes
import ctypes.util
import sys
import time
import hashlib

from pathlib import Path
BASE_DIR = Path(__file__).parent

IPV6_EXT_HEADERS = {
            0,  # Hop-by-Hop Options
            43,  # Routing
            44,  # Fragment
            51,  # Authentication Header
            60,  # Destination Options
        }
SWEEP_INTERVAL = 10.0 # seconds

ACTIVITY_THRESHOLD = 1.0  # seconds
TIMEOUT_THRESHOLD = 60.0  # seconds
ACTIVE_TIMEOUT_THRESHOLD = 120.0 # seconds

TCP_PROTOCOL = 6
UDP_PROTOCOL = 17

ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_IPV6 = 0x86DD

snap_len = 256
promiscuous = 1
read_timeout = 1000

GREASE_VALUES = {
    0x0a0a, 0x1a1a, 0x2a2a, 0x3a3a, 0x4a4a, 0x5a5a,
    0x6a6a, 0x7a7a, 0x8a8a, 0x9a9a, 0xaaaa, 0xbaba,
    0xcaca, 0xdada, 0xeaea, 0xfafa
}

class PcapPacketHeader(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long), # time value in seconds
        ('tv_usec', ctypes.c_long), # time value in microseconds
        ('capture_len', ctypes.c_uint32), # how many bytes were captured
        ('len', ctypes.c_uint32), # the actual length of the packet before capture
    ]

class RunningStats:
    def __init__(self):
        self.minimum = float('inf')
        self.maximum = float('-inf')
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0  # sum of squared deviations

    def update(self, value):
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.M2 += delta * delta2
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)

    @property
    def variance(self):
        if self.n < 2:
            return 0.0
        return self.M2 / self.n

    @property
    def std(self):
        return self.variance ** 0.5

    @property
    def max(self):
        return self.maximum if self.n > 0 else 0.0

    @property
    def min(self):
        return self.minimum if self.n > 0 else 0.0


def parse_ipv4(ipv4_bytes):
    ip_start = 14
    ip_header_len = (ipv4_bytes[ip_start] & 0x0F) * 4

    protocol = ipv4_bytes[ip_start + 9]  # 6 will be TCP and 17 will be UDP

    source_ip = ipv4_bytes[ip_start + 12: ip_start + 16]
    destination_ip = ipv4_bytes[ip_start + 16: ip_start + 20]

    flags_and_offset = int.from_bytes(ipv4_bytes[ip_start + 6:ip_start + 8], byteorder='big')
    mf_flag = (flags_and_offset >> 13) & 0x1
    fragment_offset = flags_and_offset & 0x1FFF

    if fragment_offset != 0:
        return None

    transport_start = ip_start + ip_header_len
    source_port = int.from_bytes(ipv4_bytes[transport_start:transport_start + 2], byteorder='big')
    destination_port = int.from_bytes(ipv4_bytes[transport_start + 2:transport_start + 4], byteorder='big')

    return source_ip, destination_ip, source_port, destination_port, protocol, transport_start, mf_flag

def parse_ipv6(ipv6_bytes):
    ipv6_start = 14

    source_ip = ipv6_bytes[ipv6_start + 8:ipv6_start + 24]
    destination_ip = ipv6_bytes[ipv6_start + 24:ipv6_start + 40]
    next_header = ipv6_bytes[ipv6_start + 6]

    offset = ipv6_start + 40

    while next_header in IPV6_EXT_HEADERS:
        if offset >= len(ipv6_bytes):
            return None
        if next_header == 44:
            next_header = ipv6_bytes[offset]
            offset += 8
        else:
            next_header = ipv6_bytes[offset]
            extension_length = (ipv6_bytes[offset + 1] + 1) * 8
            offset += extension_length

    source_port = int.from_bytes(ipv6_bytes[offset:offset + 2], byteorder='big')
    destination_port = int.from_bytes(ipv6_bytes[offset + 2:offset + 4], byteorder='big')

    return source_ip, destination_ip, source_port, destination_port, next_header, offset

def parse_ja3(raw_bytes, transport_start):
    try:
        payload_start = transport_start + 20
        if len(raw_bytes) < payload_start + 10:
            return None

        if raw_bytes[payload_start] != 0x16:
            return None
        if raw_bytes[payload_start + 5] != 0x01:
            return None

        position = payload_start + 9

        if position + 2 > len(raw_bytes):
            return None

        tls_version = int.from_bytes(raw_bytes[position:position+2], 'big')
        position += 2

        position += 32

        if position >= len(raw_bytes):
            return None

        session_id_len = raw_bytes[position]
        position += 1 + session_id_len

        if position + 2 > len(raw_bytes):
            return None

        cipher_len = int.from_bytes(raw_bytes[position:position+2], 'big')
        position += 2
        ciphers = []
        end = position + cipher_len
        while position + 1 < end and position + 1 < len(raw_bytes):
            c = int.from_bytes(raw_bytes[position:position+2], 'big')
            if c not in GREASE_VALUES:
                ciphers.append(c)
            position += 2
        position = end

        if position >= len(raw_bytes):
            ja3_str = f'{tls_version},{'-'.join(map(str, ciphers))},,,'
            return hashlib.md5(ja3_str.encode()).hexdigest()

        comp_len = raw_bytes[position]
        position += 1 + comp_len

        if position + 2 > len(raw_bytes):
            ja3_str = f'{tls_version},{'-'.join(map(str, ciphers))}...'
            return hashlib.md5(ja3_str.encode()).hexdigest()

        ext_total_len = int.from_bytes(raw_bytes[position:position+2], 'big')
        position += 2

        extensions = []
        curves = []
        point_formats = []
        end_ext = position + ext_total_len

        while position + 4 <= end_ext and position + 4 <= len(raw_bytes):
            ext_type = int.from_bytes(raw_bytes[position:position+2], 'big')
            ext_len = int.from_bytes(raw_bytes[position+2:position+4], 'big')
            position += 4

            if ext_type not in GREASE_VALUES:
                extensions.append(ext_type)

            if ext_type == 0x000a:
                if position + 2 <= len(raw_bytes):
                    curves_len = int.from_bytes(raw_bytes[position:position+2], 'big')
                    for i in range(2, curves_len + 2, 2):
                        if position + i + 1 < len(raw_bytes):
                            g = int.from_bytes(raw_bytes[position+i:position+i+2], 'big')
                            if g not in GREASE_VALUES:
                                curves.append(g)

            if ext_type == 0x000b:
                if position < len(raw_bytes):
                    fmt_len = raw_bytes[position]
                    for i in range(1, fmt_len + 1):
                        if position + i < len(raw_bytes):
                            point_formats.append(raw_bytes[position+i])

            position += ext_len

        ja3_str = (
            f'{tls_version},'
            f'{'-'.join(map(str, ciphers))},'
            f'{'-'.join(map(str, extensions))},'
            f'{'-'.join(map(str, curves))},'
            f'{'-'.join(map(str, point_formats))}'
        )
        return hashlib.md5(ja3_str.encode()).hexdigest()

    except Exception as e:
        print(f'Error: {e}')

def get_flow(flow_id, flow_state):
    if flow_id in flow_state:
        return flow_state[flow_id]

    flow_state[flow_id] = {
        # identity
        "src_ip": None,
        "dst_ip": None,
        "src_port": None,
        "dst_port": None,
        "protocol": None,

        # counters
        "fwd_packets": 0,
        "bwd_packets": 0,
        "fwd_bytes": 0,
        "bwd_bytes": 0,
        "current_active": 0.0,

        # running stats
        "total_byte_stats": RunningStats(),
        "fwd_byte_stats": RunningStats(),
        "bwd_byte_stats": RunningStats(),
        "total_iat_stats": RunningStats(),
        "fwd_iat_stats": RunningStats(),
        "bwd_iat_stats": RunningStats(),
        "fwd_iat_total": 0.0,
        "bwd_iat_total": 0.0,
        "active_stats": RunningStats(),
        "idle_stats": RunningStats(),

        # tcp only
        "syn_count": 0,
        "ack_count": 0,
        "fin_count": 0,
        "rst_count": 0,

        # timestamps
        "start_time": None,
        "last_seen": None,

        # JA3 Hash, computed separately
        "ja3_hash": None,
    }

    return flow_state[flow_id]

def make_canonical(flow_id):
    src_ip, dst_ip, src_port, dst_port, proto = flow_id

    if (src_ip, src_port) < (dst_ip, dst_port):
        return src_ip, dst_ip, src_port, dst_port, proto

    return dst_ip, src_ip, dst_port, src_port, proto

def capture_process(queue, stop_capture, interface_type, interface=None, pcap_file=None): # other type is live-capture
    flow_state = {}  # 6 tuple - flow dicts (flow_key: state)
    epoch_counters = {} # (traditional 5 tuple: epoch id)
    last_sweep = None

    if sys.platform == 'win32':
        libpcap = ctypes.CDLL(r'C:\Windows\System32\Npcap\wpcap.dll')
        libpcap.pcap_open_offline.restype = ctypes.c_void_p
        libpcap.pcap_open_live.restype = ctypes.c_void_p
        libpcap.pcap_next_ex.restype = ctypes.c_int
    elif sys.platform == 'linux':
        libpcap = ctypes.CDLL('libpcap.so')
    else:
        libpcap = ctypes.CDLL(ctypes.util.find_library('pcap'))

    error_buffer = ctypes.create_string_buffer(256)
    libpcap.pcap_next_ex.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.POINTER(PcapPacketHeader)),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))
    ]
    libpcap.pcap_next_ex.restype = ctypes.c_int

    if interface_type == 'simulation':
        if pcap_file:
            try:
                handle = libpcap.pcap_open_offline(pcap_file, error_buffer)
            except FileNotFoundError:
                print(f'Pcap file not found: {str(pcap_file.decode())}')
                return
            except Exception as e:
                print(f'Error opening pcap file: {e}')
                return
        else:
            PCAP_PATH = BASE_DIR.parent / 'datasets' / 'raw' / 'pcaps' / 'FIRST-2015_Hands-on_Network_Forensics_PCAP' / '2015-03-05' / 'snort.log.1425565276'
            handle = libpcap.pcap_open_offline(str(PCAP_PATH).encode(), error_buffer)
    elif interface_type == 'live-capture':
        handle = libpcap.pcap_open_live(interface, snap_len, promiscuous, read_timeout, error_buffer)
    else:
        return

    if not handle:
        raise RuntimeError(f'Failed to open pcap: {error_buffer.value.decode()}')
    handle = ctypes.c_void_p(handle)

    header = ctypes.POINTER(PcapPacketHeader)()
    data = ctypes.POINTER(ctypes.c_ubyte)()

    while True:
        if stop_capture and stop_capture.is_set():
            time.sleep(0.1)
            continue
        result = libpcap.pcap_next_ex(
            handle,
            ctypes.byref(header),
            ctypes.pointer(data)
        )
        if result != 1:
            break

        raw_bytes = bytes(data[:header[0].capture_len])
        ethertype = int.from_bytes(raw_bytes[12:14], byteorder='big')

        if ethertype != ETHERTYPE_IPV4 and ethertype != ETHERTYPE_IPV6:
            continue

        if ethertype == ETHERTYPE_IPV4:
            result = parse_ipv4(raw_bytes)
            if result is None:
                continue
            source_ip, destination_ip, source_port, destination_port, protocol, transport_start, mf_flag = result
            # may not use mf_flag right now, but when it is one, it will indicate it is the start of a fragment

        if ethertype == ETHERTYPE_IPV6:
            result = parse_ipv6(raw_bytes)
            if result is None:
                continue
            source_ip, destination_ip, source_port, destination_port, protocol, transport_start = result

        if protocol != TCP_PROTOCOL and protocol != UDP_PROTOCOL:
            continue

        if protocol == TCP_PROTOCOL:
            flags = raw_bytes[transport_start + 13]
            fin = (flags & 0x01) != 0
            syn = (flags & 0x02) != 0
            rst = (flags & 0x04) != 0
            ack = (flags & 0x10) != 0

        if protocol == UDP_PROTOCOL:
            fin = 0
            syn = 0
            rst = 0
            ack = 0

        flow_id = (source_ip, destination_ip, source_port, destination_port, protocol)
        canonical = make_canonical(flow_id)
        epoch_id = epoch_counters.get(canonical, 0)

        flow_key = (epoch_id,) + canonical
        flow = get_flow(flow_key, flow_state)

        current_timestamp = header[0].tv_sec + header[0].tv_usec / 1e6
        last_seen = flow['last_seen']

        if last_sweep is None:
            last_sweep = current_timestamp

        if current_timestamp - last_sweep >= SWEEP_INTERVAL:
            last_sweep = current_timestamp
            to_export = [ # find all flows that have passed the active timeout threshold, store in this list
                (k, v) for k, v in flow_state.items()
                if v['start_time'] is not None and
                   current_timestamp - v['start_time'] >= ACTIVE_TIMEOUT_THRESHOLD
            ]
            for swept_key, swept_flow in to_export:
                if swept_flow['fwd_packets'] + swept_flow['bwd_packets'] > 0:
                    queue.put(swept_flow)
                del flow_state[swept_key]
                swept_canonical = swept_key[1:]
                epoch_counters[swept_canonical] = swept_key[0] + 1

        while last_seen is not None and current_timestamp - last_seen >= TIMEOUT_THRESHOLD:
            if flow_key in flow_state:
                if flow['fwd_packets'] + flow['bwd_packets'] > 0:
                    queue.put(flow)
                del flow_state[flow_key]

            epoch_id += 1
            epoch_counters[canonical] = epoch_id
            flow_key = (epoch_id,) + canonical
            flow = get_flow(flow_key, flow_state)
            last_seen = flow['last_seen']

        if protocol == TCP_PROTOCOL and (source_port == 443 or destination_port == 443):
            if flow['ja3_hash'] is None:
                ja3 = parse_ja3(raw_bytes, transport_start)
                if ja3 is not None:
                    flow['ja3_hash'] = ja3

        if flow['src_ip'] is None and flow['dst_ip'] is None and flow['src_port'] is None and flow['dst_port'] is None and flow['protocol'] is None:
            flow['src_ip'] = source_ip
            flow['dst_ip'] = destination_ip
            flow['src_port'] = source_port
            flow['dst_port'] = destination_port
            flow['protocol'] = protocol

        direction = 'fwd' if (source_ip == flow['src_ip']) and (source_port == flow['src_port']) else 'bwd'
        num_bytes = header[0].len

        flow[f'{direction}_packets'] += 1
        flow[f'{direction}_bytes'] += num_bytes
        flow[f'{direction}_byte_stats'].update(num_bytes)
        flow['total_byte_stats'].update(num_bytes)

        if last_seen is not None:
            IAT = current_timestamp - last_seen
            flow['total_iat_stats'].update(IAT)
            flow[f'{direction}_iat_stats'].update(IAT)
            flow[f'{direction}_iat_total'] += IAT

            if IAT < ACTIVITY_THRESHOLD:
                flow['current_active'] += IAT
            else:
                if flow['current_active'] > 0:
                    flow['active_stats'].update(flow['current_active'])
                    flow['current_active'] = 0.0
                flow['idle_stats'].update(IAT)

        flow['syn_count'] += syn
        flow['ack_count'] += ack
        flow['fin_count'] += fin
        flow['rst_count'] += rst

        if last_seen is None:
            flow['start_time'] = current_timestamp
        flow['last_seen'] = current_timestamp

        if rst or fin:
            if flow_key in flow_state:
                queue.put(flow)
                del flow_state[flow_key]
                epoch_counters[canonical] = epoch_id + 1