"""This module manages the mockingbird object and interfaces."""

import logging
import multiprocessing
import threading
from multiprocessing import Process, Queue
from typing import Dict, List, Optional

from .config import Config
from .errors import MockingbirdUndefinedBeak
from .logger import configure_log, logger_main
from .mockingbird import Mockingbird


def mock_main(stop: threading.Event, config: Config, mb_name: str) -> None:
    """Main function loop for Mockingbird process."""

    try:
        # Create the logging process
        log_q = Queue()  # type: Queue[Optional[logging.LogRecord]]
        log_process = Process(target=logger_main, args=(log_q, mb_name))
        log_process.start()

        # Configure the log of this process.
        configure_log(log_q)
        log = logging.getLogger(mb_name)
        log.info('Booting mockingbird')

        
        mockingbird = Mockingbird(mb_name, log_q, config)

        with mockingbird:
            stop.wait()

    except (KeyboardInterrupt, SystemExit):
        pass  # Prevent stack trace caused by keyboard interrupt
    finally:
        try:
            log.info('Mockingbird shut down')
        except NameError:
            pass  # Log wan't defined yet
        try:  # Attempt to stop logging process when exiting
            log_q.put(None)
            log_process.join(5)
        except NameError:
            pass  # log_q or log_process weren't defined yet
