"""Test tcp_server.py"""

import socket

import pytest

from atticus.interfaces.tcp_server import TCPServer

HOST = '127.0.0.1'
PORT = 42826


@pytest.fixture
def tcp_server():
    """Tcp server that is not running."""
    return TCPServer({'name': 'test_tcp_interface', 'type': 'tcp_server', 'address': HOST, 'port': PORT})


@pytest.fixture(scope='function')
def running_tcp_server(tcp_server):
    """Start the tcp server."""

    with tcp_server:
        yield tcp_server


@pytest.fixture(scope='function')
def client_and_server(running_tcp_server):
    """Return connected client and TCP server."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        yield (client, running_tcp_server)


class TestTCPServer:
    """Test TCP Server"""

    def test_connect(self, running_tcp_server):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            assert sock.connect_ex((HOST, PORT)) == 0

    def test_receive(self, client_and_server):
        client, _ = client_and_server
        client.sendall(bytes('hello world', 'utf8'))

        # Wait for tcp server to have processed input
        TCPServer.input_ready.wait(5)

        msg, _ = TCPServer.read_buffer()
        assert msg == 'hello world'

    def test_respond(self, client_and_server):
        client, _ = client_and_server
        client.sendall(bytes('foo', 'utf8'))

        # Wait for tcp server to have processed input
        TCPServer.input_ready.wait(5)

        _, respond = TCPServer.read_buffer()
        respond('bar')

        assert client.recv(16) == b'bar'
