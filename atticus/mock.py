from copy import deepcopy
from time import sleep
from multiprocessing import Value
from threading import Event, Thread
from typing import Dict

from mockingbird import MockingBird
from tcp_server import TCPServer


def mock(stop: Value, config: Dict) -> None:
    """ Start communication interface and initialize mockingbird request API. """

    mockingbird = MockingBird(requests=deepcopy(config['requests']), props=deepcopy(config['properties']))
    
    stop_event = Event()
    interface = TCPServer(stop_event, deepcopy(config['interface']['tcp']), mockingbird)
    interface_thread = Thread(target=interface.start)
    interface_thread.start()

    while not stop.value:
        sleep(0.05)
        continue

    stop_event.set()
    interface_thread.join()
