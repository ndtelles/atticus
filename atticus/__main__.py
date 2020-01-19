"""Provides the entry-point to Atticus when run from the command line."""

import multiprocessing as mp

from .shell import Shell


def main() -> None:
    """Start interactive Atticus shell"""

    shl = Shell()
    try:
        shl.cmdloop()
    except (KeyboardInterrupt, SystemExit):
        shl.do_exit('')


if __name__ == '__main__':
    mp.set_start_method('spawn')
    main()
