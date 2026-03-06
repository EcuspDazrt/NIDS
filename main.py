from multiprocessing import Process, Queue
from capture.capture import capture_process
from inference.inference import inference_process
from gui.app import dashboard_process

if __name__ == "__main__":
    flow_queue = Queue()
    results_queue = Queue()

    capture = Process(target=capture_process, args=(flow_queue, 'simulation'))
    inference = Process(target=inference_process, args=(flow_queue, results_queue))
    dashboard = Process(target=dashboard_process, args=(results_queue,))

    capture.start()
    inference.start()
    dashboard.start()

    capture.join()
    inference.join()
    dashboard.join()