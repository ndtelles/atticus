"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import re
from typing import Any, Dict

from .config import parse_file
from .errors import (MockingbirdAlreadyLoaded, MockingbirdInvalidName,
                     MockingbirdNotFound, MockingbirdNotRunning,
                     MockingbirdRunning)
from .mockingbird_process import MockingbirdProcess


class Atticus:
    """Provides the Atticus API."""

    def __init__(self) -> None:
        """Atticus constructor."""
        self._mb_procs = {}  # type: Dict[str, MockingbirdProcess]

    def __del__(self) -> None:
        """Make sure all processes are stopped and joined nicely."""

        self.stop_all()

    def load(self, mb_name: str, file: str) -> None:
        """Load and parse the specified configuration file."""

        if re.match(r'^\w+$', mb_name) is None:
            raise MockingbirdInvalidName(mb_name)

        if mb_name in self._mb_procs:
            raise MockingbirdAlreadyLoaded(mb_name)

        config = parse_file(file)

        self._mb_procs[mb_name] = MockingbirdProcess(config, mb_name)

    def unload(self, mb_name: str) -> None:
        """Remove the mockingbird with the provided name."""

        if mb_name not in self._mb_procs:
            raise MockingbirdNotFound(mb_name)

        if self._mb_procs[mb_name].status is MockingbirdProcess.Status.RUNNING:
            raise MockingbirdRunning(mb_name)

        del self._mb_procs[mb_name]

    def start(self, mb_name: str) -> None:
        """Start the simulator with the provided name."""

        if mb_name not in self._mb_procs:
            raise MockingbirdNotFound(mb_name)

        process = self._mb_procs[mb_name]
        if process.status is MockingbirdProcess.Status.RUNNING:
            raise MockingbirdRunning(mb_name)

        process.start()

    def stop(self, mb_name: str) -> None:
        """Stop the simulator with the provided name."""

        if mb_name not in self._mb_procs:
            raise MockingbirdNotFound(mb_name)

        process = self._mb_procs[mb_name]
        if process.status is not MockingbirdProcess.Status.RUNNING:
            raise MockingbirdNotRunning(mb_name)

        process.stop()

    def stop_all(self) -> None:
        """Stop all _mb_processes."""

        for mb_name, process in self._mb_procs.items():
            if process.status is MockingbirdProcess.Status.RUNNING:
                self.stop(mb_name)

    def status(self, *args: str) -> Dict[str, Dict[str, Any]]:
        """Return the status of mockingbirds."""

        statuses = {}

        mb_names = args if args else self._mb_procs.keys()

        for mb_name in mb_names:
            if mb_name not in self._mb_procs:
                raise MockingbirdNotFound(mb_name)

            process = self._mb_procs[mb_name]
            statuses[mb_name] = {
                'status': process.status.name
            }

        return statuses
