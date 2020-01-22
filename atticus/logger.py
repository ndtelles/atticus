"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging
import logging.handlers
from multiprocessing import Queue


def logger_main(queue: Queue, name: str) -> None:

    _listener_configure(name)
    while True:
        try:
            record = queue.get()
            if record is None:  # Send None to the logger to exit the process
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except (KeyboardInterrupt, SystemExit):
            pass  # Parent thread will handle stopping the logger process


def _listener_configure(name: str) -> None:
    """Configure root log that all other loggers pass up to."""

    # Sanatize filename
    okay_chars = (' ', '.', '_')
    filename = ''.join(char for char in name if char.isalnum()
                       or char in okay_chars).rstrip()

    root = logging.getLogger()

    # Rotate log files with a max size of 5MB per file
    handler = logging.handlers.RotatingFileHandler(filename + '.log',
                                                   maxBytes=5242880, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def configure_log(log_q: Queue) -> None:
    handler = logging.handlers.QueueHandler(log_q)
    logger = logging.getLogger()

    # If multiprocessing is using fork (the default on Unix) instead of spawn,
    # the child process will end up inheriting the parent's handlers. To keep
    # that from happening clear existing handlers when configure is called.
    logger.handlers.clear()

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
