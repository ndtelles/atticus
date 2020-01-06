"""This module manages the mockingbird object and interfaces."""

import logging
from copy import deepcopy
from multiprocessing import Value
from typing import Dict

from .errors import BufferMissingError
from .interfaces.beak import Beak
from .interfaces.tcp_server import TCPServer
from .mockingbird import Mockingbird


def mock(stop: Value, config: Dict, mb_name: str) -> None:
    """Start communication interface and initialize mockingbird request API."""

    configure_log(mb_name)

    try:
        logging.info('Booting mockingbird')

        mockingbird = Mockingbird(requests=deepcopy(
            config['requests']), props=deepcopy(config['properties']))

        interface = TCPServer(deepcopy(config['interfaces'][0]))

        with interface:
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
                        logging.warning('Output buffer missing')
    except (KeyboardInterrupt, SystemExit):
        pass  # Prevent stack trace caused by keyboard interrupt
    finally:
        logging.info('Mockingbird process ended')


def configure_log(mb_name: str) -> None:
    """Configure the logger to be used by this mockingbird process."""

    root = logging.getLogger()
    # Rotate log files with a max size of 5MB per file
    handler = logging.handlers.RotatingFileHandler(mb_name + '.log',
                                                   maxBytes=5242880, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
