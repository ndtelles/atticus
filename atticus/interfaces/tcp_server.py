"""TCP communication interface for clients to talk to the Mockingbird server."""

import errno
import selectors
import socket
from typing import Any

from .beak import Beak


class TCPServer(Beak):
    """Class that provides TCP socket communication for making requests to the mockingbird."""

    BUFFER_SIZE = 4096
    MAX_BIND_TRIES = 100
    SELECT_TIMEOUT = 0.001

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.sel = selectors.DefaultSelector()
        self.server_sock = self._create_socket()

    def __del__(self) -> None:
        super().__del__()
        self.sel.close()

    def _start(self) -> None:
        """Start the tcp server."""

        self._bind_socket(self._config['address'], self._config['port'])
        self.server_sock.listen(10)

    def _run(self) -> None:
        """Run one iteration of the TCP server.

        First the server finds all connections that have new data to send and sets them to
        read/write mode. Then the server looks for any read or write events and handles the
        socket io.
        """

        # Check for output buffer new data notifications
        for conn in self._output_buffers.new_data():
            # Set connections with data to output to read/write
            self.sel.modify(conn, selectors.EVENT_READ |
                            selectors.EVENT_WRITE, self._socket_io)

        events = self.sel.select(TCPServer.SELECT_TIMEOUT)
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    def _stop(self) -> None:
        """Stops the TCP server and closes any open IO."""

        print("Stopping the TCP Server")
        self._close_socket()

    def _socket_io(self, conn: socket.socket, mask: int) -> None:
        """Evaluate the selector mask to decide between reading from and writing to the client."""

        if mask & selectors.EVENT_READ:
            self._socket_receive(conn)
        elif mask & selectors.EVENT_WRITE:
            self._socket_send(conn)

    def _socket_receive(self, conn: socket.socket) -> None:
        """Receive data from the selected client."""

        data = conn.recv(TCPServer.BUFFER_SIZE)
        if data:
            print("Received request:", data)
            self._receive(data.decode('utf-8', 'replace'), conn)
        else:
            print("Client disconnected")
            self._remove_client(conn)

    def _socket_send(self, conn: socket.socket) -> None:
        """Send data from the output buffer to the selected client."""

        msg = self._output_buffers.pop(conn)

        if msg is not None:
            conn.sendall(bytes(msg, 'utf8'))
            print("Sent message:", msg)

        if self._output_buffers.is_empty(conn):
            # Nothing more to send. Set to read only
            self.sel.modify(conn, selectors.EVENT_READ, self._socket_io)

    def _create_socket(self) -> socket.socket:
        """Create a new socket for clients to connect to."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        self.sel.register(sock, selectors.EVENT_READ, self._accept_client)
        return sock

    def _accept_client(self, sock: socket.socket, _: int) -> None:
        """Accept incoming client connections."""

        conn, address = sock.accept()
        print("Accepted client", address[0], address[1])
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self._socket_io)
        self._output_buffers.create(conn)

    def _remove_client(self, conn: socket.socket) -> None:
        """Remove a client from the TCP server."""

        self.sel.unregister(conn)
        self._output_buffers.delete(conn)

    def _bind_socket(self, addr: str, req_port: int) -> None:
        """Bind socket to provided ip address and port.

        If port is not available incrementally search for an open port.
        """

        port = req_port
        while True:
            try:
                self.server_sock.bind((addr, port))
                print('Socket bound on port', port)
                break
            except socket.error as ex:
                print('Socket failed to bind on port', port)
                if ex.errno == errno.EADDRINUSE and port < req_port + TCPServer.MAX_BIND_TRIES:
                    port += 1
                else:
                    raise

    def _close_socket(self) -> None:
        """Close the provided socket, freeing up the port."""

        self.sel.unregister(self.server_sock)
        self.server_sock.shutdown(socket.SHUT_RDWR)
        self.server_sock.close()
        print('Socket closed')
