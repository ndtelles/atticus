"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import pytest

from atticus.mockingbird_process import MockingbirdProcess


@pytest.fixture
def simple_mockingbird_process(simple_config):
    return MockingbirdProcess(simple_config, 'test_mockingbird')


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

    def test_restart(self, simple_running_mockingbird_process):
        """Make sure mockingbird process can start again after being stopped."""
        simple_running_mockingbird_process.stop()
        simple_running_mockingbird_process.start()
        assert simple_running_mockingbird_process.status is MockingbirdProcess.Status.RUNNING
        assert simple_running_mockingbird_process._process.is_alive()
