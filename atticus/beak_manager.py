"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import queue
import threading
from multiprocessing import Event, Process, Queue
from typing import Any, Dict, KeysView
from typing import Optional as Opt
from typing import Tuple

from .config import Config
from .errors import MockingbirdUndefinedBeak
from .helpers import drain_queue
from .interfaces.beak import Beak
from .interfaces.tcp_server_beak import TCPServerBeak
from .logger import configure_log


class BeakManager:
    class BeakProcess:
        def __init__(self, if_config: Config.Interface) -> None:
            self.config = if_config
            self.process = Process()
            self.tx_q = Queue(256)  # type: Queue[Tuple[Any, str]]
            self.running = False
            self.stop_event = Event()

    def __init__(self, log_queue: queue.Queue, config: Config) -> None:
        self._beak_procs = {}  # type: Dict[str,BeakManager.BeakProcess]

        # All beaks share buffer to help increase FIFO fidelity
        # Queue for interfaces to send received requests to mockingbird
        self._rx_q = Queue(1024)  # type: Queue[Tuple[str, Any, str]]
        # Queue for interfaces to register requests with mockingbird

        self._rr_q = Queue(256)  # type:Queue[Tuple[str,Opt[str],Opt[str]]]
        self._log_queue = log_queue

        for interface in config.interfaces:
            self.register_interface(interface)

    @property
    def register_request_queue(self) -> Queue:
        return self._rr_q

    @property
    def request_queue(self) -> Queue:
        return self._rx_q

    @property
    def interfaces(self) -> KeysView[str]:
        return self._beak_procs.keys()

    def get_reponse_queue(self, interface: str) -> queue.Queue:
        return self._beak_procs[interface].tx_q

    def register_interface(self, if_config: Config.Interface) -> None:
        self._beak_procs[if_config.name] = BeakManager.BeakProcess(if_config)

    def start_all(self) -> None:
        for _, beak_proc in self._beak_procs.items():
            if beak_proc.running:
                continue

            beak_proc.stop_event.clear()
            # interface.tx_q = Queue(256)
            beak_proc.process = Process(
                target=beak_main,
                args=(beak_proc.stop_event,
                      beak_proc.config,
                      self._log_queue,
                      beak_proc.tx_q,
                      self._rx_q,
                      self._rr_q))
            beak_proc.process.start()
            beak_proc.running = True

    def stop_all(self) -> None:
        for _, beak_proc in self._beak_procs.items():
            if not beak_proc.running:
                continue

            beak_proc.stop_event.set()
            beak_proc.process.join()
            beak_proc.running = False

        # Drain queues to prevent blocking when this process is joined
        drain_queue(self._rr_q)
        drain_queue(self._rx_q)


def beak_main(stop: threading.Event, config: Config.Interface, log_q: Queue,
              rx_q: Queue, tx_q: Queue, rr_q: Queue) -> None:
    try:
        configure_log(log_q)
        beak = create_beak(config, rx_q, tx_q, rr_q)

        # Run the interface until stop signal received. The beak interfaces
        # run their own thread, so this thread is free to idle or possibly
        # handle something else in the future.
        with beak:
            stop.wait()

    except (KeyboardInterrupt, SystemExit):
        pass  # Prevent stack trace caused by keyboard interrupt
    finally:
        # Drain queues so the parent process doesn't block while trying to
        # join this process
        drain_queue(rx_q)

        # Let parent thread handle the joining of these queues
        tx_q.cancel_join_thread()
        rr_q.cancel_join_thread()


def create_beak(config: Config.Interface, rx_q: Queue, tx_q: Queue, rr_q: Queue) -> Beak:
    # Create callable methods for Beak so that Beak is not dependant on the
    # implementation of multiprocessing
    def request(key: Any, msg: str) -> None:
        tx_q.put((config.name, key, msg))

    def receive(block: bool, timeout: Opt[float]) -> Opt[Tuple[Any, str]]:
        try:
            return rx_q.get(block, timeout)
        except queue.Empty:
            return None

    def register_request(request: str, response: Opt[str]) -> None:
        rr_q.put((config.name, request, response))

    def register_default_request(response: str) -> None:
        rr_q.put((config.name, None, response))

    if config.beak_type == 'tcp_server':
        return TCPServerBeak(config, request, receive, register_request,
                             register_default_request)

    raise MockingbirdUndefinedBeak
