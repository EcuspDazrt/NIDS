import ctypes
import ctypes.util
import sys

IPV6_EXT_HEADERS = {
            0,  # Hop-by-Hop Options
            43,  # Routing
            44,  # Fragment
            51,  # Authentication Header
            60,  # Destination Options
        }

TCP_PROTOCOL = 6
UDP_PROTOCOL = 17

ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_IPV6 = 0x86DD

network_interface = b'eth0'
snap_len = 256
promiscuous = 1
read_timeout = 1000

class PcapPacketHeader(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long), # time value in seconds
        ('tv_usec', ctypes.c_long), # time value in microseconds
        ('capture_len', ctypes.c_uint32), # how many bytes were captured
        ('len', ctypes.c_uint32), # the actual length of the packet before capture
    ]

class RunningStats:
    def __init__(self):
        self.minimum = None
        self.maximum = None
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0  # sum of squared deviations

    def update(self, value):
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.M2 += delta * delta2

        if self.minimum is None:
            self.minimum = value
        else:
            self.minimum = min(self.minimum, value)

        if self.maximum is None:
            self.maximum = value
        else:
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
        return self.maximum

    @property
    def min(self):
        return self.minimum


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
    }

    return flow_state[flow_id]

def make_flow_key(flow_id):
    epoch, src_ip, dst_ip, src_port, dst_port, proto = flow_id

    if (src_ip, src_port) < (dst_ip, dst_port):
        return epoch, src_ip, dst_ip, src_port, dst_port, proto

    return epoch, dst_ip, src_ip, dst_port, src_port, proto

def capture_process(queue, interface_type=None): # other type is live-capture
    flow_state = {}  # 6 tuple: flow dicts (flow_key: state)

    if sys.platform == 'win32':
        libpcap = ctypes.CDLL(r'C:\Windows\System32\Npcap\wpcap.dll')
    else:
        libpcap = ctypes.CDLL(ctypes.util.find_library('pcap'))

    error_buffer = ctypes.create_string_buffer(256)

    if interface_type == 'simulation':
        handle = libpcap.pcap_open_offline(b'datasets/raw/pcaps/FIRST-2015_Hands-on-Network_Forensics_PCAP/2015-03-05/snort.log.1425565276', error_buffer)
    elif interface_type == 'live-capture':
        handle = libpcap.pcap_open_live(network_interface, snap_len, promiscuous, error_buffer)
    else:
        return

    if not handle:
        print(f'Error: {error_buffer.value.decode()}')

    header = ctypes.POINTER(PcapPacketHeader)()
    data = ctypes.POINTER(ctypes.c_ubyte)()

    while True:
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

        epoch_id = 0
        ACTIVITY_THRESHOLD = 1.0 # seconds
        TIMEOUT_THRESHOLD = 60.0 # seconds

        # increment epoch flow id until it hits a flow that is not timed out
        flow_id = epoch_id, source_ip, destination_ip, source_port, destination_port, protocol
        flow_key = make_flow_key(flow_id)
        flow = get_flow(flow_key, flow_state)

        current_timestamp = header[0].tv_sec + header[0].tv_usec / 1e6
        last_seen = flow['last_seen']

        while last_seen is not None and current_timestamp - last_seen >= TIMEOUT_THRESHOLD:
            flow_id = (epoch_id, source_ip, destination_ip, source_port, destination_port, protocol)
            flow_key = make_flow_key(flow_id)
            flow = get_flow(flow_key, flow_state)
            last_seen = flow['last_seen']
            epoch_id += 1

        # get the first flow that is not timed-out
        flow_id = (epoch_id, source_ip, destination_ip, source_port, destination_port, protocol)
        flow_key = make_flow_key(flow_id)
        flow = get_flow(flow_key, flow_state)
        last_seen = flow['last_seen']

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

        queue.put(flow)

# from multiprocessing import Process, Queue
# queue = Queue()
# capture_process(queue, interface_type='simulation')