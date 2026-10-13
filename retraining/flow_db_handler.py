import sqlite3
import util.paths as p

from retraining.retrain_ae import log_retrain_event
from util.logger import get_logger
LOGGER = get_logger(__name__)

def get_num_flows():
    with sqlite3.connect(p.FLOW_DB_PATH) as conn:
        total = conn.execute('''
                SELECT count(*) FROM flow_logs
            ''').fetchone()[0]

    return total

def get_days_available(temp_iso):
    with sqlite3.connect(p.FLOW_DB_PATH) as conn:
        if temp_iso:
            days_available = conn.execute('''
                SELECT COUNT(DISTINCT date(timestamp)) FROM flow_logs
                WHERE timestamp < datetime('now', '-24 hours')
                AND timestamp > datetime('now', '-7 days')
            ''').fetchone()[0]
        else:
            days_available = conn.execute('''
                SELECT COUNT(DISTINCT date(timestamp)) FROM flow_logs
                WHERE timestamp > datetime('now', '-7 days')
                        ''').fetchone()[0]

    return days_available


def get_ae_samples(temp_iso, flow_ids=None):
    id_filter = ''
    if flow_ids is not None:
        placeholders = ','.join('?' * len(flow_ids))
        id_filter = f'AND id IN ({placeholders})'

    params = tuple(flow_ids) if flow_ids else ()

    if temp_iso:
        query = f'''
            SELECT ae_features FROM flow_logs
            WHERE rf_category = 0
            AND timestamp < datetime('now', '-24 hours')
            AND timestamp > datetime('now', '-7 days')
            {id_filter}
        '''
    else:
        query = f'''
            SELECT ae_features FROM flow_logs
            WHERE rf_category = 0
            AND timestamp > datetime('now', '-7 days')
            {id_filter}
        '''

    try:
        with sqlite3.connect(p.FLOW_DB_PATH) as conn:
            ae_samples = conn.execute(query, params).fetchall()
    except Exception:
        message = 'no eligible samples after filtering'
        log_retrain_event(0, None, None, 0, message)
        LOGGER.error(message)
        return None

    return ae_samples


def get_drift_check_samples():
    with sqlite3.connect(p.FLOW_DB_PATH) as conn:
        recent = conn.execute('''
                    SELECT ae_category, COUNT(*) as count
                    FROM flow_logs
                    WHERE timestamp > datetime('now', '-2 hours')
                    GROUP BY ae_category
                ''').fetchall()

        historical = conn.execute('''
                    SELECT ae_category, COUNT(*) as count
                    FROM flow_logs
                    WHERE timestamp > datetime('now', '-7 days')
                    AND timestamp < datetime('now', '-2 hours')
                    GROUP BY ae_category
                ''').fetchall()

    return recent, historical

def get_validation_samples():
    with sqlite3.connect(p.FLOW_DB_PATH) as conn:
        samples = conn.execute('''
            SELECT ae_features FROM flow_logs
            WHERE rf_category = 0
            AND ae_features IS NOT NULL
            AND timestamp > datetime('now', '-24 hours')
            LIMIT 500
        ''').fetchall()

    return samples