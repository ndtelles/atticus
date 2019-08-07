"""Test tcp_server.py"""

import socket

import pytest

from .conftest import HOST, PORT


@pytest.mark.incremental
class TestTCPServer:
    """Test TCP Server"""

    def test_tcp_lifecycle(self, basic_tcp_server):
        """Test creation, binding, and destruction of sockets used by TCPServer"""

        # Socket creation. Check that file descriptor has been created
        server_socket = basic_tcp_server.create_socket()
        assert server_socket.fileno() != -1

        # Socket connection
        basic_tcp_server.bind_socket(server_socket, HOST, PORT)
        server_socket.listen(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            assert sock.connect_ex((HOST, PORT)) == 0

        # Socket closing
        basic_tcp_server.close_socket(server_socket)
        assert server_socket.fileno() == -1
