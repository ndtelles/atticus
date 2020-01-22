"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from queue import Queue

import pytest

from atticus import config
from atticus.beak_manager import create_beak


def pytest_runtest_makereport(item, call):
    """Add support for incremental mark."""

    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    """Add support for incremental mark."""

    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


@pytest.fixture
def simple_config_file():
    return './tests/test_configs/simple_tcp.yaml'


@pytest.fixture
def simple_config(simple_config_file):
    return config.parse_file(simple_config_file)


@pytest.fixture
def beak_factory():
    def _make_beak(config):
        tx_q = Queue()
        rx_q = Queue()
        rr_q = Queue()
        bk = create_beak(config, tx_q, rx_q, rr_q)
        return bk, rx_q, tx_q, rr_q
    return _make_beak
