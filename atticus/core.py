"""Atticus API used for creating and controlling mockingbirds."""

from typing import Dict

from .device_config import parse_file
from .errors import (MockingbirdAlreadyLoaded, MockingbirdNotFound,
                     MockingbirdNotRunning, MockingbirdRunning)
from .mockingbird_process import MockingbirdProcess


class Atticus:
    """Provides the Atticus API."""

    def __init__(self) -> None:
        """Atticus constructor."""
        self._mb_processes = {}

    def __del__(self) -> None:
        """Make sure all processes are stopped and joined nicely when Atticus is deconstructed."""

        self.stop_all()

    def load(self, file: str) -> str:
        """Load and parse the specified configuration file."""

        config = parse_file(file)
        mb_name = config.get('name')

        if any(mb.name == mb_name for mb in self._mb_processes):
            raise MockingbirdAlreadyLoaded(mb_name)

        self._mb_processes[mb_name] = MockingbirdProcess(config)
        return mb_name

    def unload(self, mb_name: str) -> None:
        """Remove the mockingbird with the provided name."""

        if mb_name not in self._mb_processes:
            raise MockingbirdNotFound(mb_name)

        if self._mb_processes.get(mb_name).status is MockingbirdProcess.Status.RUNNING:
            raise MockingbirdRunning(mb_name)

        del self._mb_processes[mb_name]

    def start(self, mb_name: str) -> None:
        """Start the simulator with the provided name."""

        if mb_name not in self._mb_processes:
            raise MockingbirdNotFound(mb_name)

        process = self._mb_processes.get(mb_name)
        if process.status is MockingbirdProcess.Status.RUNNING:
            raise MockingbirdRunning(mb_name)

        process.start()

    def stop(self, mb_name: str) -> None:
        """Stop the simulator with the provided name."""

        if mb_name not in self._mb_processes:
            raise MockingbirdNotFound(mb_name)

        process = self._mb_processes.get(mb_name)
        if process.status is not MockingbirdProcess.Status.RUNNING:
            raise MockingbirdNotRunning(mb_name)

        process.stop()

    def stop_all(self, ) -> None:
        """Stop all _mb_processes. This function is called when exiting Atticus."""

        for mb_name, process in self._mb_processes.items():
            if process.status is MockingbirdProcess.Status.RUNNING:
                self.stop(mb_name)

    def status(self, *args: str) -> Dict:
        """Return the status of mockingbirds."""

        statuses = {}

        mb_names = args if args else self._mb_processes.keys()

        for mb_name in mb_names:
            if mb_name not in self._mb_processes:
                raise MockingbirdNotFound(mb_name)

            process = self._mb_processes.get(mb_name)
            statuses[mb_name] = {
                'status': process.status.name
            }

        return statuses
