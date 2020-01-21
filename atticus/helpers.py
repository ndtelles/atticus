import queue
from multiprocessing import Queue


def drain_queue(q: Queue) -> None:
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass
