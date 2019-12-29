"""Test mockingbird_process.py"""

import pytest

from atticus.mockingbird_process import MockingbirdProcess


@pytest.fixture
def simple_mockingbird_process(simple_config):
    return MockingbirdProcess(simple_config)


@pytest.fixture
def simple_running_mockingbird_process(simple_mockingbird_process):
    simple_mockingbird_process.start()
    return simple_mockingbird_process


class TestMockingbirdProcess:
    """Test Mockingbird Process"""

    def test_start(self, simple_mockingbird_process):
        simple_mockingbird_process.start()
        assert simple_mockingbird_process.status is MockingbirdProcess.Status.RUNNING
        assert simple_mockingbird_process._process.is_alive()

    def test_stop(self, simple_running_mockingbird_process):
        simple_running_mockingbird_process.stop()
        assert simple_running_mockingbird_process.status is MockingbirdProcess.Status.STOPPED
        assert not simple_running_mockingbird_process._process.is_alive()
