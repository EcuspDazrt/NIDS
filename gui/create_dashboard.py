from multiprocessing import Process
import pystray
from PIL import Image, ImageDraw
import threading
import time

from pathlib import Path
BASE_DIR = Path(__file__).parent

from gui.app import dashboard_process

def create_tray_icon(results_queue, stop_capture, models_ready, alert_engine, flash_event):
    dashboard_proc = [None]  # mutable container so inner functions can modify it

    def open_dashboard(icon, item):
        if dashboard_proc[0] is None or not dashboard_proc[0].is_alive():
            dashboard_proc[0] = Process(
                target=dashboard_process,
                args=(results_queue, stop_capture, models_ready)
            )
            dashboard_proc[0].start()

    def stop_system(icon, item):
        icon.stop()
        if dashboard_proc[0] and dashboard_proc[0].is_alive():
            dashboard_proc[0].terminate()

    # simple colored circle as tray icon
    def make_icon(base_img, color):
        img = base_img.copy().convert('RGBA').resize((64, 64))
        draw = ImageDraw.Draw(img)
        draw.ellipse([44, 44, 60, 60], fill=color + (255,), outline=(15, 17, 23, 255))
        return img

    def poll_status(icon, base_img):
        while not icon.visible:
            time.sleep(0.1)
        while icon.visible:
            if models_ready.is_set():
                icon.icon = make_icon(base_img, (87, 168, 122))   # green when ready
                icon.title = 'NIDS — Monitoring'
                icon._update_icon()
            else:
                icon.icon = make_icon(base_img, (184, 148, 42))   # amber while loading
                icon.title = 'NIDS — Loading...'
            time.sleep(2.0)

    def poll_flash(icon, base_img):
        while not icon.visible:
            time.sleep(0.1)
        while icon.visible:
            if flash_event.wait(timeout=1.0):
                flash_event.clear()
                flash_alert()

    def flash_alert():
        if not icon.visible:
            return
        for _ in range(6):
            icon.icon = make_icon(icon_img, (184, 64, 64))
            try:
                icon._update_icon()
            except Exception:
                pass
            time.sleep(0.4)
            icon.icon = make_icon(icon_img, (87, 168, 122))
            try:
                icon._update_icon()
            except Exception:
                pass
            time.sleep(0.4)

    def retrain_loop():
        drift_check_interval = 7200 # 7200; 2 hours
        retrain_check_interval = 86400 # 86400; 1 day
        rollback_cooldown = 172800 # 172800; 2 days
        last_rollback_time = None
        last_retrain_check = 0

        while True:
            time.sleep(drift_check_interval)
            try:
                from scripts.retrain_ae import check_drift
                drift_detected = check_drift(alert_engine)
            except Exception as e:
                print(f'Drift check failed: {e}')
                drift_detected = False

            now = time.time()
            if now - last_retrain_check >= retrain_check_interval:
                last_retrain_check = now
                if drift_detected:
                    from scripts.retrain_ae import log_retrain_event, rollback_ae
                    message = 'skipped: drift detected, training date may be contaminated'
                    log_retrain_event(0, None, None, 0, message)

                    if last_rollback_time and time.time() - last_rollback_time < rollback_cooldown:
                        message = 'skipped: within rollback cooldown period'
                        log_retrain_event(0, None, None, 0, message)
                        continue

                    success = rollback_ae()
                    last_rollback_time = time.time()
                    if success:
                        message = 'rolled back: drift detected in current model'
                        log_retrain_event(0, None, None, 0, message)
                        if alert_engine:
                            alert_engine.signal_rollback('AE model rolled back due to detected drift')
                    else:
                        message = 'drift detected but no valid backup available for rollback'
                        log_retrain_event(0, None, None, 0, message)
                else:
                    try:
                        from scripts.retrain_ae import try_retrain
                        try_retrain()
                    except Exception as e:
                        print(f'Retraining check failed: {e}')

    menu = pystray.Menu(
        pystray.MenuItem('Open Dashboard', open_dashboard, default=True),
        pystray.MenuItem('Stop NIDS', stop_system)
    )

    icon_img = Image.open(BASE_DIR.parent/'gui'/'resources'/'nids_icon.ico').resize((256, 256))
    icon = pystray.Icon(
        'NIDS',
        make_icon(icon_img, (184, 148, 42)),
        'NIDS — Monitoring',
        menu
    )

    threading.Thread(target=retrain_loop, daemon=True).start()
    threading.Thread(target=poll_status, args=(icon,icon_img), daemon=True).start()
    threading.Thread(target=poll_flash, args=(icon, icon_img), daemon=True).start()
    icon.run()
