"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import queue
from multiprocessing import Queue


def drain_queue(q: Queue) -> None:
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass
