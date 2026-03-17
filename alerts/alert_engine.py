from collections import deque

class AlertEngine:
    def __init__(self, rf_threshold, ae_threshold, results_queue):
        self.recent_ae = deque(maxlen=10)
        self.results_queue = results_queue
        self.alerted = False
        self.rf_threshold = rf_threshold
        self.ae_threshold = ae_threshold

    def evaluate(self, ae_category, rf_category, rf_score, ja3_hash, ja3_malicious):
        self.recent_ae.append(ae_category)

        if rf_category >= self.rf_threshold:
            self._fire({
                'type': 'EXPLICIT_ATTACK_DETECTION',
                'severity': rf_category,
                'message': f'Known attack pattern detected (RF score: {rf_score:.3f})',
            })
            self.alerted = False

        if len(self.recent_ae) >= 10:
            severe_count = sum(1 for s in self.recent_ae if s >= self.ae_threshold)
            if severe_count >= 6 and not self.alerted:
                self._fire({
                    'type': 'SYSTEMIC_ANOMALY',
                    'severity': 3,
                    'message': f'Sustained anomalous traffic: {severe_count}/10 recent flows flagged',
                })
                self.alerted = True
            elif severe_count < 4:
                self.alerted = False

        if ja3_malicious:
            self._fire({
                'type': 'JA3_MATCH',
                'severity':4,
                'message': f'Known malware TLS fingerprint matched: {ja3_hash}',
            })
    def _fire(self, alert):
        from datetime import datetime, timezone
        from alerts.logger import log_alert, write_alert

        alert['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_alert(alert)
        write_alert(alert)
        try:
            self.results_queue.put({'type':'alert','payload':alert})
        except Exception as e:
            print(f'Error when queueing alert: {e}')