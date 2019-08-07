"""This module manages the mockingbird object and interfaces."""

from copy import deepcopy
from multiprocessing import Value
from threading import Event, Thread
from time import sleep
from typing import Dict

from .mockingbird import Mockingbird
from .tcp_server import TCPServer


def mock(stop: Value, config: Dict) -> None:
    """Start communication interface and initialize mockingbird request API."""

    try:
        mockingbird = Mockingbird(requests=deepcopy(
            config['requests']), props=deepcopy(config['properties']))

        stop_event = Event()
        interface = TCPServer(stop_event, deepcopy(
            config['interface']['tcp']), mockingbird)
        interface_thread = Thread(target=interface.start)
        interface_thread.start()

        while not stop.value:
            sleep(0.05)
            continue
    finally:
        stop_event.set()
        interface_thread.join()
