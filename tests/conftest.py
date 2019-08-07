"""Configuration for pytest"""

import threading

import pytest

from atticus import mockingbird, tcp_server

HOST = '127.0.0.1'
PORT = 42826


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
def blank_mockingbird():
    """Create simple mockingbird object."""

    return mockingbird.Mockingbird(None, None)


@pytest.fixture
def basic_tcp_server(blank_mockingbird):
    """Create simple tcp server."""

    stop_event = threading.Event()
    return tcp_server.TCPServer(stop_event, {'address': HOST, 'port': PORT}, blank_mockingbird)
