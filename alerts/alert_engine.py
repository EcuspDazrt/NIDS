from collections import deque
from datetime import datetime, timedelta
from alerts.logger import ip_to_str

class AlertEngine:
    def __init__(self, rf_threshold, ae_threshold, results_queue, flash_event=None):
        self.recent_ae = deque(maxlen=10)
        self.results_queue = results_queue
        self.alerted = False
        self.rf_threshold = rf_threshold
        self.ae_threshold = ae_threshold
        self.last_ae_notification = None
        self._flash_event = flash_event
        self.AE_COOLDOWN = timedelta(minutes=10)

    def _should_notify_ae(self):
        if self.last_ae_notification is None:
            return True
        return datetime.now() - self.last_ae_notification > self.AE_COOLDOWN

    def evaluate(self, ae_category, rf_category, rf_score, ja3_hash, ja3_malicious, flow):
        self.recent_ae.append(ae_category)

        if rf_category >= self.rf_threshold:
            src = flow.get('src_ip')
            dst = flow.get('dst_ip')
            self._fire({
                'type': 'EXPLICIT_ATTACK_DETECTION',
                'severity': rf_category,
                'message': f'Known attack pattern detected (RF score: {rf_score:.3f})',
                'flow_src': ip_to_str(src) if isinstance(src, bytes) else str(src),
                'flow_dst': ip_to_str(dst) if isinstance(dst, bytes) else str(dst),
            })
            self.alerted = False

        if len(self.recent_ae) >= 10 and self._should_notify_ae():
            severe_count = sum(1 for s in self.recent_ae if s >= self.ae_threshold)
            if severe_count >= 6 and not self.alerted:
                src = flow.get('src_ip')
                dst = flow.get('dst_ip')
                self._fire({
                    'type': 'SYSTEMIC_ANOMALY',
                    'severity': 3,
                    'message': f'Sustained anomalous traffic: {severe_count}/10 recent flows flagged',
                    'flow_src': ip_to_str(src) if isinstance(src, bytes) else str(src),
                    'flow_dst': ip_to_str(dst) if isinstance(dst, bytes) else str(dst),
                })
                self.last_ae_notification = datetime.now()
                self.alerted = True
            elif severe_count < 4:
                self.alerted = False

        if ja3_malicious:
            src = flow.get('src_ip')
            dst = flow.get('dst_ip')
            self._fire({
                'type': 'JA3_MATCH',
                'severity':4,
                'message': f'Known malware TLS fingerprint matched: {ja3_hash}',
                'flow_src': ip_to_str(src) if isinstance(src, bytes) else str(src),
                'flow_dst': ip_to_str(dst) if isinstance(dst, bytes) else str(dst),
            })

    def signal_drift(self, reason):
        self._fire({
            'type': 'MODEL_DRIFT_DETECTION',
            'severity':2,
            'message': reason,
            'flow_src': None,
            'flow_dst': None,
        })

    def signal_rollback(self, reason):
        self._fire({
            'type': 'MODEL_ROLLBACK',
            'severity': 2,
            'message': reason,
            'flow_src': None,
            'flow_dst': None,
        })

    def set_flash_event(self, event):
        self._flash_event = event

    def _fire(self, alert):
        from datetime import datetime, timezone
        from alerts.logger import log_alert, write_alert, send_system_notification

        alert['timestamp'] = datetime.now(timezone.utc).isoformat()

        log_alert(alert)
        write_alert(alert)

        if self._flash_event:
            self._flash_event.set()

        if alert['flow_src'] is not None and alert['flow_dst'] is not None:
            send_system_notification(alert)
        try:
            self.results_queue.put({'type':'alert','payload':alert})
        except Exception as e:
            print(f'Error when queueing alert: {e}')