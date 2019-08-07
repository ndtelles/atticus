"""Provides multiprocessing control for atticus"""

from enum import Enum
from multiprocessing import Process, Value
from typing import Dict

from .mock import mock


class MockingbirdProcess:
    """Class for controlling the child mockingbird processes created by atticus"""

    JOIN_TIMEOUT = 5

    class Status(Enum):
        """Enum class representing the status of the mockingbird process."""

        STOPPED = 0
        RUNNING = 1

    def __init__(self, config: Dict) -> None:
        """ The constructor of the Mockingbird Process class """

        self.config = config
        self.status = MockingbirdProcess.Status.STOPPED
        self.stop_event = Value('i', 0)
        self.process = Process(target=mock, args=(
            self.stop_event, self.config))

    def start(self) -> None:
        """ Start the process """

        self.stop_event.value = 0
        self.status = MockingbirdProcess.Status.RUNNING
        self.process.start()

    def stop(self) -> None:
        """ Stop the process """

        self.stop_event.value = 1
        self.process.join(MockingbirdProcess.JOIN_TIMEOUT)

        if not self.process.is_alive():
            self.status = MockingbirdProcess.Status.STOPPED
