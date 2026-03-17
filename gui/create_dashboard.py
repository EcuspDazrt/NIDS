from multiprocessing import Process
import pystray
from PIL import Image, ImageDraw
import threading

from gui.app import dashboard_process

def create_tray_icon(results_queue, stop_capture, models_ready):
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
    def make_icon(color):
        img = Image.new('RGB', (64, 64), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=color)
        return img

    def poll_status(icon):
        while icon.visible:
            if models_ready.is_set():
                icon.icon = make_icon((87, 168, 122))   # green when ready
            else:
                icon.icon = make_icon((184, 148, 42))   # amber while loading
            threading.Event().wait(2.0)

    menu = pystray.Menu(
        pystray.MenuItem('Open Dashboard', open_dashboard, default=True),
        pystray.MenuItem('Stop NIDS', stop_system)
    )

    icon = pystray.Icon(
        'NIDS',
        make_icon((184, 148, 42)),
        'NIDS — Loading...',
        menu
    )

    threading.Thread(target=poll_status, args=(icon,), daemon=True).start()
    icon.run()
