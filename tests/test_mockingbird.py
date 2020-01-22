"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


from queue import Queue

import pytest

from atticus.errors import MockingbirdUndefinedVar
from atticus.mockingbird import Mockingbird

INTERFACE = 'tcp_test_interface'


@pytest.fixture
def simple_mockingbird(simple_config):
    return Mockingbird('test_mb', Queue(), simple_config)


@pytest.fixture
def simple_registered_mockingbird(simple_mockingbird):
    """Mocking bird with simple requests registered"""
    mb = simple_mockingbird
    mb._register_request(INTERFACE, 'units $(unit)', '$(unit)')
    mb._register_request(INTERFACE, 'units?', '$(unit)')
    mb._register_request(INTERFACE, 'set phasers_mode $(phasers_mode)', 'OK')
    mb._register_request(INTERFACE, 'set coordinates $(x) $(y)', '$(x) $(y)')
    mb._register_request(INTERFACE, 'get coordinates', '$(x) $(y)')
    mb._register_request(INTERFACE, 'version', '1.0.0')
    mb._register_request(INTERFACE, None, 'invalid')
    return mb


class TestMockingbird:
    """Test Mockingbird"""

    def test_vars_created(self, simple_mockingbird):
        assert 'unit' in simple_mockingbird._mb_vars

    def test_vars_init_value(self, simple_mockingbird):
        assert simple_mockingbird._mb_vars['unit'].value == 0

    def test_register_request(self, simple_mockingbird):
        """Make sure requests are registered properly."""
        mb = simple_mockingbird
        mb._register_request(INTERFACE, 'units $(unit)', '$(unit)')

        request = mb._requests[INTERFACE].list[0]
        assert request._raw_request == 'units $(unit)'
        assert len(request._req_vars) == 1
        assert 'unit' in request._req_vars

        assert request._raw_response == '$(unit)'
        assert len(request._resp_vars) == 1
        assert 'unit' in request._resp_vars
        assert request._response == '{}'

    def test_register_default_request(self, simple_mockingbird):
        mb = simple_mockingbird
        mb._register_request(INTERFACE, None, '$(unit)')
        assert INTERFACE in mb._default_responses

        request = mb._default_responses[INTERFACE]
        assert request._raw_response == '$(unit)'
        assert 'unit' in request._resp_vars
        assert len(request._resp_vars) == 1
        assert request._response == '{}'

    def test_request_interface_and_key(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'version')
        _, beak, key, _ = mb._response_queue.get()
        assert beak == INTERFACE
        assert key == 'my_key'

    def test_default_request(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'blahblahblahblah')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == 'invalid'

    def test_request_no_var(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'version')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '1.0.0'

    def test_request_in_var(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'set phasers_mode kill')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == 'OK'

    def test_request_out_var(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'units?')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '0'

    def test_request_in_and_out_var(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'units 5')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '5'

    def test_request_multiple_vars(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'set coordinates 56.0766 37.1062')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '56.0766 37.1062'

    def test_var_persistance(self, simple_registered_mockingbird):
        mb = simple_registered_mockingbird
        mb._request(INTERFACE, 'my_key', 'set coordinates 56.0766 37.1062')
        mb._request(INTERFACE, 'my_key', 'get coordinates')
        mb._response_queue.get()
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '56.0766 37.1062'

    def test_escape_curly_braces(self, simple_mockingbird):
        mb = simple_mockingbird
        mb._register_request(INTERFACE, 'units {} $(unit)', '{}$(unit)')
        mb._request(INTERFACE, 'my_key', 'units {} 5')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '{}5'

    def test_escape_curly_braces2(self, simple_mockingbird):
        mb = simple_mockingbird
        mb._register_request(
            INTERFACE, '{{}}units {{{}}{}} $(unit){}}', '{{}}$(unit)}{{{}{}}}')
        mb._request(INTERFACE, 'my_key', '{{}}units {{{}}{}} 5{}}')
        _, _, _, req = mb._response_queue.get()
        assert req.build_response(mb._mb_vars) == '{{}}5}{{{}{}}}'

    def test_undefined_in(self, simple_mockingbird):
        mb = simple_mockingbird
        with pytest.raises(MockingbirdUndefinedVar):
            mb._register_request(INTERFACE, 'units $(fake_var)', '$(unit)')

    def test_undefined_out(self, simple_mockingbird):
        mb = simple_mockingbird
        with pytest.raises(MockingbirdUndefinedVar):
            mb._register_request(INTERFACE, 'units $(unit)', '$(fake_var)')
