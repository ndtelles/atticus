import sys
from multiprocessing import Process, Value
from typing import List

from device_config import parse_file
from mock import mock


def main(config_files: List[str]) -> None:
    """ Create a process to run each device in the provided config files. """

    processes = []
    for f in config_files:
        config = parse_file(f)
        if not config:
            print("Invalid config file", f)
            continue
        
        stop = Value('i', 0)
        p = Process(target=mock, args=(stop, config))
        p.start()
        processes.append((p, stop))
    
    input("")

    for p, stop in processes:
        stop.value = 1
        p.join()

if __name__ == '__main__':
    main(sys.argv[1:])
