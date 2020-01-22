"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from enum import Enum
from multiprocessing import Event, Process

from .config import Config
from .mock import mock_main


class MockingbirdProcess:
    """Class for controlling mockingbird processes created by atticus"""

    class Status(Enum):
        """Enum class representing the status of the mockingbird process."""

        STOPPED = 0
        RUNNING = 1

    def __init__(self, config: Config, mb_name: str) -> None:
        """ The constructor of the Mockingbird Process class """
        self._status = MockingbirdProcess.Status.STOPPED
        self._config = config
        self._mb_name = mb_name
        self._stop_event = Event()
        self._process = Process()

    def __del__(self) -> None:
        self.stop()

    def _create_process(self) -> Process:
        return Process(target=mock_main, args=(
            self._stop_event, self._config, self._mb_name))

    @property
    def status(self) -> 'MockingbirdProcess.Status':
        """Getter for status"""

        return self._status

    def start(self) -> None:
        """ Start the process """

        if self._status is MockingbirdProcess.Status.RUNNING:
            return

        self._stop_event.clear()
        self._status = MockingbirdProcess.Status.RUNNING
        self._process = self._create_process()
        self._process.start()

    def stop(self) -> None:
        """ Stop the process """

        if self._status is MockingbirdProcess.Status.STOPPED:
            return

        self._stop_event.set()
        self._process.join()

        self._status = MockingbirdProcess.Status.STOPPED
