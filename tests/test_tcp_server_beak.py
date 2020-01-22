"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import socket

import pytest


@pytest.fixture
def tcp_server(simple_config, beak_factory):
    """Tcp server that is not running."""
    return beak_factory(list(simple_config.interfaces)[0])


@pytest.fixture(scope='function')
def running_tcp_server(tcp_server):
    """Start the tcp server."""

    with tcp_server[0]:
        yield tcp_server


@pytest.fixture(scope='function')
def client_and_server(running_tcp_server):
    """Return connected client and TCP server."""
    server, rx_q, tx_q, rr_q = running_tcp_server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(server.server_address)
        yield client, server, rx_q, tx_q, rr_q


class TestTCPServer:
    """Test TCP Server"""

    def test_connect(self, running_tcp_server):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            assert sock.connect_ex(running_tcp_server[0].server_address) == 0

    def test_request(self, client_and_server):
        client, _, rx_q, _, _ = client_and_server
        client.sendall(bytes('hello world\r\n', 'utf8'))

        # Wait for tcp server to have processed input
        # Check what tcp server tries to send mockingbird
        interface, _, msg = rx_q.get(timeout=1)

        assert interface == 'tcp_test_interface'
        assert msg == 'hello world'

    def test_respond(self, client_and_server):
        client, _, rx_q, tx_q, _ = client_and_server
        client.sendall(bytes('foo\r\n', 'utf8'))

        # Wait for tcp server to have processed input
        _, key, _ = rx_q.get(timeout=1)
        tx_q.put((key, 'bar'))

        assert client.recv(16) == b'bar\r\n'
