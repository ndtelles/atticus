"""Configuration for pytest"""

import threading

import pytest

from atticus import mockingbird, config, mockingbird_process
from atticus.interfaces.tcp_server import TCPServer

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
def simple_config():
    return config.parse_file('./test_configs/simple_tcp.yaml')

@pytest.fixture
def simple_mockingbird_process(simple_config):
    return mockingbird_process.MockingbirdProcess(simple_config)

@pytest.fixture
def blank_mockingbird():
    """Create simple mockingbird object."""

    return mockingbird.Mockingbird(None, None)


@pytest.fixture
def simple_tcp_server(blank_mockingbird):
    """Create simple tcp server."""

    return TCPServer({'address': HOST, 'port': PORT})
