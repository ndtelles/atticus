"""TCP interface for clients to talk to the Mockingbird server."""

import errno
import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
from threading import Event, Thread
from typing import Any, Callable, Dict
from uuid import uuid4

from .beak import Beak


class TCPServerBeak(Beak, ThreadingTCPServer):  # type: ignore

    # Threading TCP Server attributes
    allow_reuse_address = True

    # Name of this attribute changes in Python 3.7
    _block_on_close = True
    block_on_close = True

    daemon_threads = False

    # TCPServerBeak attributes
    MAX_BIND_TRIES = 10

    def __init__(self, *args: Any) -> None:
        Beak.__init__(self, *args)
        address = (self._config.props['address'], self._config.props['port'])
        ThreadingTCPServer.__init__(self, address, _TCPHandler, False)

        self.server_thread = Thread(target=self.serve_forever)
        self.consumer_thread = Thread(target=self.mb_receive_loop)
        self.bind_tries = TCPServerBeak.MAX_BIND_TRIES

    def _boot_beak(self) -> None:
        if b'\\' in self._config.props['line_ending'].encode('utf8', 'ignore'):
            self._log.warning(
                'Escaped characters detected in line ending.'
                ' Wrap line ending in double quotes in YAML config.')

        self._log.info('Registering requests')

        requests = self._config.props.get('requests', [])
        for request in requests:
            self._mb_register_request(request['in'], request['out'])

        self._mb_register_default_request(
            self._config.props['default_response'])

        # TODO: Requests are not guaranteed to be actually registered by
        # mockingbird at this point. There should be some kind of confirmation
        # when requests are registered that the boot process can wait on

        self._log.info('Booting server')
        self._log.info('Attempting to bind socket to %s port %d',
                       *self.server_address)

        self.bind_with_incrementing_port()

        self._log.info('Socket bound to %s: %d', *self.server_address)

    def _run_beak(self) -> None:
        self.server_thread.start()
        self.consumer_thread.start()
        self._log.info('Server started')

    def _shutdown_beak(self) -> None:
        self._log.info('Shutting down server')

        # Stop consumer thread before server so consumer thread doesn't try to
        # send responses to no longer existing clients after server has stopped
        self.consumer_thread.join()

        # Stop the server
        self.shutdown()
        self.server_thread.join()

        self._log.info('Server shutdown')

    def bind_with_incrementing_port(self) -> None:
        while True:
            try:
                self.server_bind()

                # Rarely, even when server bind succeeds, calling server
                # activate fails with errno.EADDRINUSE.
                self.server_activate()
                break
            except socket.error as ex:
                # Keep trying ports until we run out of tries
                if ex.errno == errno.EADDRINUSE and self.bind_tries >= 1:
                    addr, port = self.server_address
                    self._log.warning('Failed to bind port %d', port)
                    self.server_address = (addr, port + 1)
                    self.reset()
                    self.bind_tries -= 1
                else:
                    self._log.critical('Failed to bind to any port')
                    raise

    def reset(self) -> None:
        self.socket.close()
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)

    def mb_receive_loop(self) -> None:
        while not self._stop_event.is_set():
            mb_response = self._mb_receive(True, 0.5)
            if mb_response is not None:
                _TCPHandler.respond(*mb_response)


class _TCPHandler(BaseRequestHandler):
    """Handle clients that connect to the TCP server

    A TCP Handler is instantiated in a new thread each time a client connects
    to the TCP server.
    """

    TIMEOUT = 0.5

    # Limit size of buffer so a client spamming data without line endings
    # can't crash the program by using all of the available memory
    MAX_BUFFER_SIZE = 16384

    clients = {}  # type: Dict[str, '_TCPHandler']

    @staticmethod
    def respond(key: str, msg: str) -> None:
        """Allows server to respond to a client with a mockingbird response"""
        handler = _TCPHandler.clients.get(key, None)

        if handler is None:  # Connection was dropped
            return

        handler.response = msg
        handler.respond_event.set()

    def setup(self) -> None:
        self.config = self.server.config  # type: ignore
        self.log = self.server.log  # type: ignore
        self.stop_event = self.server._stop_event  # type: ignore
        self.term = self.config.props['line_ending'].encode('utf8', 'ignore')

        self.key = str(uuid4())
        _TCPHandler.clients[self.key] = self
        self.respond_event = Event()
        self.response = ''

        self.log.info("Client %s: %d connected", *self.client_address)

    def handle(self) -> None:
        read_buffer = []
        read_buffer_len = 0

        while not self.stop_event.is_set():
            self.request.settimeout(_TCPHandler.TIMEOUT)

            try:
                # Peek at data in buffer
                peeked = self.request.recv(4096, socket.MSG_PEEK)

                if not peeked:
                    self.log.info("Client %s: %d disconnected",
                                  *self.client_address)
                    return

                # Find the position of the line ending if it exists.
                # Otherwise throw exception
                end_pos = peeked.index(self.term) + len(self.term)
            except socket.timeout:
                continue  # Try again from the top to check stop event
            except ValueError:
                # No line ending was detected in peeked data from socket.
                # Take the data read so far and store it in a buffer

                self.log.info('Received partial request from %s: %d. %s',
                              *self.client_address, peeked)
                read_buffer.append(self.request.recv(len(peeked)))
                read_buffer_len += len(peeked)

                # Disconnect client if read buffer is at its limit
                if read_buffer_len >= _TCPHandler.MAX_BUFFER_SIZE:
                    self.log.error(
                        "Client %s: %d exceeded max buffer length.",
                        *self.client_address)
                    return

                continue

            # Read all characters into buffer until line ending
            read_buffer.append(self.request.recv(end_pos))
            read_bytes = b''.join(read_buffer)

            self.log.info('Received request from %s: %d. %s',
                          *self.client_address, read_bytes)

            # Pass request data to mockingbird
            request_data = read_bytes.rstrip(
                self.term).decode('utf-8', 'ignore')
            self.server._mb_request(self.key, request_data)  # type: ignore

            # Wait for a response to be received.
            # Poll stop event to ensure exit happens if event occurs
            while not self.respond_event.wait(_TCPHandler.TIMEOUT):
                if self.stop_event.is_set():
                    return

            self.request.sendall(self.response.encode(
                'utf8', 'ignore') + self.term)

            # Prepare for next request
            self.respond_event.clear()
            read_buffer.clear()
            read_buffer_len = 0

    def finish(self) -> None:
        del _TCPHandler.clients[self.key]
