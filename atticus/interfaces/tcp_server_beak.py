"""TCP communication interface for clients to talk to the Mockingbird server."""

import errno
import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
from threading import Event, Thread
from typing import Any, Dict
from uuid import uuid4

from .beak import Beak


class TCPServerBeak(Beak, ThreadingTCPServer):

    # Threading TCP Server attributes
    allow_reuse_address = True
    block_on_close = False  # Makes sure we have consistent behavior between Python versions

    # TCPServerBeak attributes
    max_bind_tries = 10
    default_response = ''

    def __init__(self, *args: Any) -> None:
        Beak.__init__(self, *args)
        ThreadingTCPServer.__init__(
            self, (self._config.props['address'], self._config.props['port']), _TCPHandler, False)

        self.server_thread = Thread(target=self.serve_forever)
        # Exit the server thread when the main thread terminates
        # self.server_thread.daemon = True

        self.consumer_thread = Thread(target=self.mb_receive_loop)
        # self.consumer_thread.daemon = True

    def server_bind(self) -> None:
        """Called to bind the socket. Overriden from ThreadingTCPServer class

        Added feature: If port is not available incrementally search for an open port.
        """

        addr, req_port = self.server_address
        port = req_port

        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._log.info('Attempting to bind socket to %s port %d',
                       *self.server_address)

        while True:
            try:
                self.socket.bind((addr, port))
                self.server_address = self.socket.getsockname()
                self._log.info('Socket bound to %s port %d',
                               *self.server_address)
                break
            except socket.error as ex:
                if ex.errno == errno.EADDRINUSE and port < req_port + TCPServerBeak.max_bind_tries:
                    self._log.warn(
                        'Socket failed to bind on port %d. Trying next port', port)
                    port += 1
                else:
                    raise

    def _boot_beak(self) -> None:
        self._log.info('Registering requests')

        requests = self._config.props.get('requests', [])
        for request in requests:
            self._mb_register_request(request['in'], request['out'])

        self._mb_register_default_request(self._config.props.get(
            'default_response', TCPServerBeak.default_response))

        # TODO: Requests are not guaranteed to be actually registered by
        # mockingbird at this point. There should be some kind of confirmation
        # when requests are registered that the boot process can wait on

        self._log.info('Booting server')
        self.server_bind()
        self.server_activate()

    def _run_beak(self) -> None:
        self.server_thread.start()
        self.consumer_thread.start()
        self._log.info('Server started')

    def _shutdown_beak(self) -> None:
        self._log.info('Shutting down server')

        # Stop consumer thread before server so the consumer thread doesn't try to
        # send responses to no longer existing clients after server has stopped
        self.consumer_thread.join()

        # Stop the server
        self.shutdown()
        self.server_thread.join()

        self._log.info('Server shutdown')

    def mb_receive_loop(self) -> None:
        while not self._stop_event.is_set():
            mb_response = self._mb_receive(True, 0.5)
            if mb_response is not None:
                _TCPHandler.respond(*mb_response)


class _TCPHandler(BaseRequestHandler):
    """Handle clients that connect to the TCP server

    A TCP Handler is instantiated in a new thread each time a client connects to the TCP server."""

    default_line_ending = '\n'
    clients = {}  # type: Dict[str, '_TCPHandler']

    @staticmethod
    def respond(key: str, msg: str) -> None:
        """Allows for the server to respond to a client with a mockingbird response"""
        handler = _TCPHandler.clients.get(key, None)

        if handler is None:
            # Client is missing, drop response
            return

        handler.response = msg
        handler.respond_event.set()

    def setup(self) -> None:
        self.connection = self.request
        self.config = self.server.config
        self.line_ending = self.config.props.get(
            'line_ending', _TCPHandler.default_line_ending)
        self.rfile = self.connection.makefile(
            'rb', -1, newline=self.line_ending)
        self.wfile = self.connection.makefile(
            'wb', 0, newline=self.line_ending)

        self.log = self.server.log

        self.key = str(uuid4())
        self.clients[self.key] = self
        self.respond_event = Event()
        self.response = ''

        self.log.info("Client connected from %s port %d", *self.client_address)

    def handle(self) -> None:
        while True:
            self.respond_event.clear()

            raw_data = self.rfile.readline()

            if not raw_data:
                self.log.info("Client from %s port %d disconnected",
                              *self.client_address)
                break

            self.log.info("Received request from %s port %d: %s",
                          self.client_address[0], self.client_address[1], raw_data)
            data = raw_data.decode('utf-8', 'replace').rstrip('\r\n')
            self.server._mb_request(self.key, data)

            self.respond_event.wait()
            self.wfile.write(bytes(self.response, 'utf8'))

    def finish(self) -> None:
        del self.clients[self.key]
        self.rfile.close()
