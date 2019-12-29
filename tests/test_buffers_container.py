"""Test buffers_container.py"""

import pytest

from atticus.errors import BufferAlreadyExists, BufferMissingError
from atticus.interfaces._helpers.buffers_container import BuffersContainer

KEY = 'my_key'
MSG = 'hello world'


@pytest.fixture
def empty_buffers_container():
    """Create buffers container with no buffers"""

    return BuffersContainer()


@pytest.fixture
def simple_buffers_container(empty_buffers_container):
    """Create buffers container with an empty buffer."""

    empty_buffers_container.create(KEY)
    return empty_buffers_container


@pytest.fixture
def simple_filled_buffers_container(simple_buffers_container):
    """Create buffers container with a buffer and one sample message. has_new_data should be true"""

    simple_buffers_container.append(KEY, MSG)
    return simple_buffers_container


class TestBuffersContainer:
    """Test Buffers container"""

    def test_create(self, empty_buffers_container):
        empty_buffers_container.create(KEY)
        assert KEY in empty_buffers_container._buffers
        assert empty_buffers_container.is_empty(KEY)

    def test_create_already_exists(self, simple_buffers_container):
        with pytest.raises(BufferAlreadyExists):
            simple_buffers_container.create(KEY)

    def test_delete(self, simple_buffers_container):
        simple_buffers_container.delete(KEY)
        assert KEY not in simple_buffers_container._buffers

    def test_delete_missing(self, empty_buffers_container):
        with pytest.raises(BufferMissingError):
            empty_buffers_container.delete('literally anything')

    def test_delete_new_data(self, simple_filled_buffers_container):
        simple_filled_buffers_container.delete(KEY)
        assert not simple_filled_buffers_container.has_new_data(KEY)

    def test_append(self, simple_buffers_container):
        simple_buffers_container.append(KEY, 'foo')
        assert simple_buffers_container._buffers[KEY][0] == 'foo'

    def test_append_missing(self, empty_buffers_container):
        with pytest.raises(BufferMissingError):
            empty_buffers_container.append('literally anything', MSG)

    def test_pop(self, simple_buffers_container):
        # Test pop works in FIFO order
        simple_buffers_container.append(KEY, 'foo')
        simple_buffers_container.append(KEY, 'bar')

        assert simple_buffers_container.pop(KEY) == 'foo'
        assert simple_buffers_container.pop(KEY) == 'bar'

    def test_pop_new_data(self, simple_filled_buffers_container):
        simple_filled_buffers_container.append(KEY, 'extra message')
        simple_filled_buffers_container.pop(KEY)
        # Since there is still data in the buffer, new data should stay true
        assert simple_filled_buffers_container.has_new_data(KEY, False)

        # When there is only one item in buffer, popping should cause new_data to be false
        simple_filled_buffers_container.pop(KEY)
        assert not simple_filled_buffers_container.has_new_data(KEY)

    def test_pop_empty(self, simple_buffers_container):
        assert simple_buffers_container.pop(KEY) is None

    def test_pop_missing(self, empty_buffers_container):
        with pytest.raises(BufferMissingError):
            empty_buffers_container.pop(KEY)

    def test_new_data(self, empty_buffers_container):
        empty_buffers_container.create('buff1')
        empty_buffers_container.append('buff1', 'foo')
        empty_buffers_container.create('buff2')
        empty_buffers_container.append('buff2', 'bar')

        new_data = empty_buffers_container.new_data()
        assert 'buff1' in new_data and 'buff2' in new_data
        # New data should be cleared after being checked
        assert not empty_buffers_container.new_data()

    def test_new_data_no_ack(self, empty_buffers_container):
        empty_buffers_container.create('buff1')
        empty_buffers_container.append('buff1', 'foo')
        empty_buffers_container.create('buff2')
        empty_buffers_container.append('buff2', 'bar')

        new_data = empty_buffers_container.new_data(False)
        assert 'buff1' in new_data and 'buff2' in new_data
        # New data should be cleared after being checked
        new_data = empty_buffers_container.new_data()
        assert 'buff1' in new_data and 'buff2' in new_data

    def test_has_new_data(self, simple_filled_buffers_container):
        assert simple_filled_buffers_container.has_new_data(KEY)
        # New data notification should clear after checking
        assert not simple_filled_buffers_container.has_new_data(KEY)

    def test_has_new_data_no_ack(self, simple_filled_buffers_container):
        assert simple_filled_buffers_container.has_new_data(KEY, False)
        assert simple_filled_buffers_container.has_new_data(KEY)

    def test_is_empty(self, simple_buffers_container):
        assert simple_buffers_container.is_empty(KEY)
        simple_buffers_container.append(KEY, MSG)
        assert not simple_buffers_container.is_empty(KEY)
        simple_buffers_container.pop(KEY)
        assert simple_buffers_container.is_empty(KEY)

    def test_is_empty_missing(self, empty_buffers_container):
        with pytest.raises(BufferMissingError):
            empty_buffers_container.is_empty(KEY)
