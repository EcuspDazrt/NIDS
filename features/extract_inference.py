import numpy as np

def extract_features_ae(flow):
    fwd = flow['fwd_packets']
    bwd = flow['bwd_packets']
    duration = flow['last_seen'] - flow['start_time']

    fwd_bytes = flow['fwd_bytes']
    bwd_bytes = flow['bwd_bytes']

    features = {
        "Duration": np.log1p(duration),
        "In/Out Ratio": np.log1p(fwd) - np.log1p(bwd),
        "Absolute Difference": abs(fwd - bwd) / (fwd + bwd + 1e-6),
        "Byte Rate Asymmetry": abs(np.log1p(fwd_bytes / (duration + 1e-6)) - np.log1p(bwd_bytes / (duration + 1e-6))),

        "Forward Packet Rate": np.log1p(fwd / (duration + 1e-6)),
        "Forward Byte Rate": np.log1p(fwd_bytes / (duration + 1e-6)),
        "Forward Byte Mean": np.log1p(flow['fwd_byte_stats'].mean),
        "Forward Byte Std": np.log1p(flow['fwd_byte_stats'].std),

        "Backward Packet Rate": np.log1p(bwd / (duration + 1e-6)),
        "Backward Byte Rate": np.log1p(bwd_bytes / (duration + 1e-6)),
        "Backward Byte Mean": np.log1p(flow['bwd_byte_stats'].mean),
        "Backward Byte Std": np.log1p(flow['bwd_byte_stats'].std),

        "Forward IAT Mean": np.log1p(flow['fwd_iat_stats'].mean),
        "Forward IAT Std": np.log1p(flow['fwd_iat_stats'].std),
        "Backward IAT Mean": np.log1p(flow['bwd_iat_stats'].mean),
        "Backward IAT Std": np.log1p(flow['bwd_iat_stats'].std),

        "Active Mean": np.log1p(flow['active_stats'].mean),
        "Active Std": np.log1p(flow['active_stats'].std),
        "Idle Mean": np.log1p(flow['idle_stats'].mean),
        "Idle Std": np.log1p(flow['idle_stats'].std),
    }

    return features

def extract_features_rf(flow):
    from features.extract_training import port_category, is_private

    fwd = flow['fwd_packets']
    bwd = flow['bwd_packets']
    fwd_bytes = flow['fwd_bytes']
    bwd_bytes = flow['bwd_bytes']
    syn = flow['syn_count']
    ack = flow['ack_count']
    fin = flow['fin_count']
    rst = flow['rst_count']
    duration = (flow['last_seen'] - flow['start_time'])
    protocol = flow['protocol']

    features = {
        'proto_0': 1 if protocol == 0 else 0,
        'proto_6': 1 if protocol == 6 else 0,
        'proto_17': 1 if protocol == 17 else 0,

        'Port': port_category(flow['dst_port']),
        # 'IP': is_private(flow['dst_ip']),
        'Duration': duration,
        'In/Out Ratio': fwd / (bwd + 1e-6),

        'Total Packets': fwd + bwd,
        'Total Bytes': fwd_bytes + bwd_bytes,
        'Total Packet Rate': (fwd + bwd) / (duration + 1e-6),
        'Total Byte Rate': (fwd_bytes + bwd_bytes) / (duration + 1e-6),
        'Total Byte Max': flow['total_byte_stats'].max,
        'Total Byte Min': flow['total_byte_stats'].min,
        'Total Byte Mean': flow['total_byte_stats'].mean,
        'Total Byte Std': flow['total_byte_stats'].std,
        'Total Byte Variance': flow['total_byte_stats'].variance,

        'Forward Packets': fwd,
        'Forward Bytes': fwd_bytes,
        'Forward Packet Rate': fwd / (duration + 1e-6),
        'Forward Byte Rate': fwd_bytes / (duration + 1e-6),
        'Forward Byte Max': flow['fwd_byte_stats'].max,
        'Forward Byte Min': flow['fwd_byte_stats'].min,
        'Forward Byte Mean': flow['fwd_byte_stats'].mean,
        'Forward Byte Std': flow['fwd_byte_stats'].std,
        'Forward Byte Variance': flow['fwd_byte_stats'].variance,

        'Backward Packets': bwd,
        'Backward Bytes': bwd_bytes,
        'Backward Packet Rate': bwd / (duration + 1e-6),
        'Backward Byte Rate': bwd_bytes / (duration + 1e-6),
        'Backward Byte Max': flow['bwd_byte_stats'].max,
        'Backward Byte Min': flow['bwd_byte_stats'].min,
        'Backward Byte Mean': flow['bwd_byte_stats'].mean,
        'Backward Byte Std': flow['bwd_byte_stats'].std,
        'Backward Byte Variance': flow['bwd_byte_stats'].variance,

        'Total IAT': flow['bwd_iat_total'] + flow['fwd_iat_total'],
        'Total IAT Max': flow['total_iat_stats'].max,
        'Total IAT Min': flow['total_iat_stats'].min,
        'Total IAT Mean': flow['total_iat_stats'].mean,
        'Total IAT Std': flow['total_iat_stats'].std,
        'Total IAT Variance': flow['total_iat_stats'].variance,

        'Forward IAT': flow['fwd_iat_total'],
        'Forward IAT Max': flow['fwd_iat_stats'].max,
        'Forward IAT Min': flow['fwd_iat_stats'].min,
        'Forward IAT Mean': flow['fwd_iat_stats'].mean,
        'Forward IAT Std': flow['fwd_iat_stats'].std,
        'Forward IAT Variance': flow['fwd_iat_stats'].variance,

        'Backward IAT': flow['bwd_iat_total'],
        'Backward IAT Max': flow['bwd_iat_stats'].max,
        'Backward IAT Min': flow['bwd_iat_stats'].min,
        'Backward IAT Mean': flow['bwd_iat_stats'].mean,
        'Backward IAT Std': flow['bwd_iat_stats'].std,
        'Backward IAT Variance': flow['bwd_iat_stats'].variance,

        'Active Max': flow['active_stats'].max,
        'Active Min': flow['active_stats'].min,
        'Active Mean': flow['active_stats'].mean,
        'Active Std': flow['active_stats'].std,
        'Active Variance': flow['active_stats'].variance,
        'Idle Max': flow['idle_stats'].max,
        'Idle Min': flow['idle_stats'].min,
        'Idle Mean': flow['idle_stats'].mean,
        'Idle Std': flow['idle_stats'].std,
        'Idle Variance': flow['idle_stats'].variance,

        'Syn Ratio': syn / (fwd + bwd + 1e-6),
        'Ack Ratio': ack / (fwd + bwd + 1e-6),
        'Fin Ratio': fin / (fwd + bwd + 1e-6),
        'Rst Ratio': rst / (fwd + bwd + 1e-6),
        'Syn Rate': syn / (duration + 1e-6),
        'Ack Rate': ack / (duration + 1e-6),
        'Fin Rate': fin / (duration + 1e-6),
        'Rst Rate': rst / (duration + 1e-6),
        'Syn/Ack Ratio': syn / (ack + 1e-6),
        'Fin/Ack Ratio': fin / (ack + 1e-6),
        'Rst/Syn Ratio': rst / (syn + 1e-6),
    }

    return features