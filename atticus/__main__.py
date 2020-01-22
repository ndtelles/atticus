"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

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
