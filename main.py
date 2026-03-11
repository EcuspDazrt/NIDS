from multiprocessing import Process, Queue, Event
from capture.capture import capture_process
from inference.inference import inference_process
from gui.app import dashboard_process
import time

if __name__ == "__main__":
    flow_queue = Queue()
    results_queue = Queue()
    stop_capture = Event()
    models_ready = Event()

    dashboard = Process(target=dashboard_process, args=(results_queue, stop_capture, models_ready))
    dashboard.start()

    time.sleep(0.5)

    capture = Process(target=capture_process, args=(flow_queue, stop_capture, 'simulation'))
    inference = Process(target=inference_process, args=(flow_queue, results_queue, models_ready))

    capture.start()
    inference.start()

    capture.join()
    inference.join()
    dashboard.join()