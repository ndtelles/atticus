"""This module manages the mockingbird object and interfaces."""

from copy import deepcopy
from multiprocessing import Value
from typing import Dict

from .errors import BufferMissingError
from .interfaces.beak import Beak
from .interfaces.tcp_server import TCPServer
from .mockingbird import Mockingbird


def mock(stop: Value, config: Dict) -> None:
    """Start communication interface and initialize mockingbird request API."""

    try:
        mockingbird = Mockingbird(requests=deepcopy(
            config['requests']), props=deepcopy(config['properties']))

        interface = TCPServer(deepcopy(config['interface']['tcp']))
        interface.start()

        while not stop.value:
            # Increase CPU efficieny by waiting for input ready event.
            # Timeout ensures stop.value gets checked.
            Beak.input_ready.wait(0.1)

            msg, respond = Beak.read_buffer()

            response = ''
            if msg is not None:
                response = mockingbird.request(msg)

            if respond is not None:
                try:
                    respond(response)
                except BufferMissingError:
                    print('Output buffer missing')
    except (KeyboardInterrupt, SystemExit):
        pass  # Prevent stack trace caused by keyboard interrupt
    finally:
        interface.stop()
