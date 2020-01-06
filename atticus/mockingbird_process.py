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

    def __init__(self, config: Dict, mb_name: str) -> None:
        """ The constructor of the Mockingbird Process class """
        self._status = MockingbirdProcess.Status.STOPPED
        self._config = config
        self._mb_name = mb_name
        self._stop_event = Value('i', 0)
        self._process = self._create_process()

    def __del__(self) -> None:
        if self._process.is_alive():
            self.stop()

    def _create_process(self) -> Process:
        return Process(target=mock, args=(
            self._stop_event, self._config, self._mb_name))

    @property
    def status(self) -> 'MockingbirdProcess.Status':
        """Getter for status"""

        return self._status

    def start(self) -> None:
        """ Start the process """

        self._stop_event.value = 0
        self._status = MockingbirdProcess.Status.RUNNING
        self._process = self._create_process()
        self._process.start()

    def stop(self) -> None:
        """ Stop the process """

        self._stop_event.value = 1
        self._process.join(MockingbirdProcess.JOIN_TIMEOUT)

        if not self._process.is_alive():
            self._status = MockingbirdProcess.Status.STOPPED
