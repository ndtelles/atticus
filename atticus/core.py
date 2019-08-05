"""Atticus API used for creating and controlling mockingbirds."""

import atexit
from typing import Dict

from .device_config import parse_file
from .errors import (MockingbirdAlreadyLoaded, MockingbirdNotFound,
                     MockingbirdNotRunning, MockingbirdRunning)
from .mockingbird_process import MockingbirdProcess

#ToDo: Convert API to class

mb_processes = {}


def load(file: str) -> str:
    """Load and parse the specified configuration file."""

    config = parse_file(file)
    mb_name = config.get('name')

    if any(mb.name == mb_name for mb in mb_processes):
        raise MockingbirdAlreadyLoaded(mb_name)

    mb_processes[mb_name] = MockingbirdProcess(config)
    return mb_name


def unload(mb_name: str) -> None:
    """Remove the mockingbird with the provided name."""

    if mb_name not in mb_processes:
        raise MockingbirdNotFound(mb_name)

    if mb_processes.get(mb_name).status is MockingbirdProcess.Status.RUNNING:
        raise MockingbirdRunning(mb_name)

    del mb_processes[mb_name]


def start(mb_name: str) -> None:
    """Start the simulator with the provided name."""

    if mb_name not in mb_processes:
        raise MockingbirdNotFound(mb_name)

    process = mb_processes.get(mb_name)
    if process.status is MockingbirdProcess.Status.RUNNING:
        raise MockingbirdRunning(mb_name)

    process.start()


def stop(mb_name: str) -> None:
    """Stop the simulator with the provided name."""

    if mb_name not in mb_processes:
        raise MockingbirdNotFound(mb_name)

    process = mb_processes.get(mb_name)
    if process.status is not MockingbirdProcess.Status.RUNNING:
        raise MockingbirdNotRunning(mb_name)

    process.stop()


@atexit.register
def stop_all() -> None:
    """Stop all _mb_processes. This function is called when exiting Atticus."""

    for mb_name, process in mb_processes.items():
        if process.status is MockingbirdProcess.Status.RUNNING:
            stop(mb_name)


def status(*args: str) -> Dict:
    """Return the status of mockingbirds."""

    statuses = {}

    mb_names = args if args else mb_processes.keys()

    for mb_name in mb_names:
        if mb_name not in mb_processes:
            raise MockingbirdNotFound(mb_name)

        process = mb_processes.get(mb_name)
        statuses[mb_name] = {
            'status': process.status.name
        }

    return statuses
