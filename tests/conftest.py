"""Configuration for pytest"""

import pytest

from atticus import config


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
