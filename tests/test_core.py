"""Test core.py"""

import pytest

from atticus import Atticus
from atticus.errors import (MockingbirdAlreadyLoaded, MockingbirdNotFound,
                            MockingbirdNotRunning, MockingbirdRunning)
from atticus.mockingbird_process import MockingbirdProcess


@pytest.fixture
def empty_atticus():
    """Create an unused Atticus object."""

    return Atticus()


@pytest.fixture
def loaded_atticus(empty_atticus, simple_config_file):
    """Create an Atticus object with a laoded config."""

    empty_atticus.load(simple_config_file)
    return empty_atticus


@pytest.fixture
def running_atticus(loaded_atticus):
    """Create an Atticus object with a running config."""

    loaded_atticus.start('test_device')
    return loaded_atticus


class TestAtticusAPI:
    """Test Atticus API"""

    def test_load(self, empty_atticus):
        mb_name = empty_atticus.load('./tests/test_configs/simple_tcp.yaml')
        assert mb_name == 'test_device'
        assert mb_name in empty_atticus._mb_processes

    def test_load_already_loaded(self, empty_atticus):
        empty_atticus.load('./tests/test_configs/simple_tcp.yaml')
        with pytest.raises(MockingbirdAlreadyLoaded):
            empty_atticus.load('./tests/test_configs/simple_tcp.yaml')

    def test_unload(self, loaded_atticus):
        mb_name = next(iter(loaded_atticus._mb_processes))
        loaded_atticus.unload(mb_name)
        assert mb_name not in loaded_atticus._mb_processes

    def test_unload_not_loaded(self, empty_atticus):
        with pytest.raises(MockingbirdNotFound):
            empty_atticus.unload('literally_anything')

    def test_unload_running(self, running_atticus):
        mb_name = next(iter(running_atticus._mb_processes))
        with pytest.raises(MockingbirdRunning):
            running_atticus.unload(mb_name)

    def test_start(self, loaded_atticus):
        mb_name = next(iter(loaded_atticus._mb_processes))
        loaded_atticus.start(mb_name)
        assert loaded_atticus._mb_processes[mb_name].status is MockingbirdProcess.Status.RUNNING

    def test_start_already_started(self, running_atticus):
        mb_name = next(iter(running_atticus._mb_processes))
        with pytest.raises(MockingbirdRunning):
            running_atticus.start(mb_name)

    def test_start_not_loaded(self, empty_atticus):
        with pytest.raises(MockingbirdNotFound):
            empty_atticus.start('literally_anything')

    def test_stop(self, running_atticus):
        mb_name = next(iter(running_atticus._mb_processes))
        running_atticus.stop(mb_name)
        assert running_atticus._mb_processes[mb_name].status is MockingbirdProcess.Status.STOPPED

    def test_stop_not_loaded(self, empty_atticus):
        with pytest.raises(MockingbirdNotFound):
            empty_atticus.stop('literally_anything')

    def test_stop_not_running(self, loaded_atticus):
        mb_name = next(iter(loaded_atticus._mb_processes))
        with pytest.raises(MockingbirdNotRunning):
            loaded_atticus.stop(mb_name)
