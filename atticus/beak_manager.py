import logging
import queue
import threading
from contextlib import AbstractContextManager
from multiprocessing import Event, Process, Queue
from types import TracebackType
from typing import Any, Dict, KeysView, Optional, Tuple, Type

from .config import Config
from .errors import MockingbirdUndefinedBeak
from .interfaces.beak import Beak
from .interfaces.tcp_server_beak import TCPServerBeak
from .logger import configure_log


class BeakManager(AbstractContextManager):
    class BeakProcess:
        def __init__(self, if_config: Config.Interface) -> None:
            self.config = if_config
            self.process = Process()
            self.tx_q = Queue(256)  # type: Queue[Tuple[Any, str]]
            self.running = False
            self.stop_event = Event()

    def __init__(self, log_queue: queue.Queue, config: Config) -> None:
        self._interfaces = {}  # type: Dict[str,BeakManager.BeakProcess]

        # All beaks share buffer to help increase FIFO fidelity
        # Queue for interfaces to send received requests to mockingbird
        self._rx_q = Queue(1024)  # type: Queue[Tuple[str, Any, str]]
        # Queue for interfaces to register requests with mockingbird

        self._rr_q = Queue(
            256)  # type:Queue[Tuple[str,Optional[str],Optional[str]]]
        self._log_queue = log_queue

        for interface in config.interfaces:
            self.register_interface(interface)

    def __enter__(self) -> 'BeakManager':
        self.start_all()
        return self

    def __exit__(self, ex: Optional[Type[BaseException]], val: Optional[BaseException],
                 trb: Optional[TracebackType]) -> None:
        self.stop_all()

    @property
    def register_request_queue(self) -> Queue:
        return self._rr_q

    @property
    def request_queue(self) -> Queue:
        return self._rx_q

    @property
    def interfaces(self) -> KeysView[str]:
        return self._interfaces.keys()

    def get_reponse_queue(self, interface: str) -> queue.Queue:
        return self._interfaces[interface].tx_q

    def register_interface(self, if_config: Config.Interface) -> None:
        self._interfaces[if_config.name] = BeakManager.BeakProcess(if_config)

    def start_all(self) -> None:
        for _, interface in self._interfaces.items():
            if interface.running:
                continue

            interface.stop_event.clear()
            # interface.tx_q = Queue(256)
            interface.process = Process(
                target=beak_main,
                args=(interface.stop_event,
                      interface.config,
                      self._log_queue,
                      interface.tx_q,
                      self._rx_q,
                      self._rr_q))
            interface.process.start()
            interface.running = True

    def stop_all(self) -> None:
        for _, interface in self._interfaces.items():
            if not interface.running:
                continue

            interface.stop_event.set()
            interface.process.join()
            interface.running = False


def beak_main(stop: threading.Event, config: Config.Interface, log_q: Queue, rx_q: Queue,
              tx_q: Queue, rr_q: Queue) -> None:
    try:
        configure_log(log_q)
        interface = create_beak(config, rx_q, tx_q, rr_q)

        # Run the interface until stop signal received. The beak interfaces
        # run their own thread, so this thread is free to idle or possibly
        # handle something else in the future.
        with interface:
            stop.wait()
    except (KeyboardInterrupt, SystemExit):
        pass  # Prevent stack trace caused by keyboard interrupt


def create_beak(config: Config.Interface, rx_q: Queue, tx_q: Queue, rr_q: Queue) -> Beak:
    # Create callable methods for Beak so that Beak is not dependant on the
    # implementation of multiprocessing
    def request(key: Any, msg: str) -> None:
        tx_q.put((config.name, key, msg))

    def receive(block: bool, timeout: Optional[float]) -> Optional[Tuple[Any, str]]:
        try:
            return rx_q.get(block, timeout)
        except queue.Empty:
            return None

    def register_request(request: str, response: Optional[str]) -> None:
        rr_q.put((config.name, request, response))

    def register_default_request(response: str) -> None:
        rr_q.put((config.name, None, response))

    if config.beak_type == 'tcp_server':
        return TCPServerBeak(config, request, receive, register_request, register_default_request)

    raise MockingbirdUndefinedBeak
