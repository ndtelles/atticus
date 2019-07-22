import errno
import selectors
import socket

from beak import Beak


class TCPServer(Beak):
    """ Class that provides TCP socket communication for making requests to the mockingbird """

    BUFFER_SIZE = 1024
    MAX_BIND_TRIES = 100
    SELECT_TIMEOUT = 0.05
    
    def start(self) -> None:
        """ Start the TCP server. """

        self.sel = selectors.DefaultSelector()

        s = self.create_socket()
        self.bind_socket(s, self.config['address'], self.config['port'])
        s.listen(10)
        
        while not self.stop_event.isSet():
            events = self.sel.select(TCPServer.SELECT_TIMEOUT)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
        
        self.close_socket(s)
        print("Stopping the TCP Server")

    def socket_io(self, conn: socket.socket, mask: bytes) -> None:
        """ Evaluate the selector mask to decide between reading from and writing to the client. """

        if mask & selectors.EVENT_READ:
            self.socket_receive(conn)
        # elif mask & selectors.EVENT_WRITE:
        #     socket_send(conn)

    def socket_receive(self, conn: socket.socket) -> None:
        """ Receive data from the connected client. """

        data = conn.recv(TCPServer.BUFFER_SIZE)
        if data:
            print("Received request:", data)
            response = self.mockingbird.request(data.decode('utf-8'))
            conn.sendall(bytes(response, 'utf8'))
            print("Sent response:", response)
        else:
            print("Client disconnected")
            self.sel.unregister(conn)

    def create_socket(self) -> socket.socket:
        """ Create a new socket for clients to connect to. """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(False)
        self.sel.register(s, selectors.EVENT_READ, self.accept_client)
        return s

    def accept_client(self, s: socket.socket, mask: int) -> None:
        """ Accept incoming client connections. """

        conn, address = s.accept()
        print("Accepted client", address[0], address[1])
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.socket_io)

    def bind_socket(self, s: socket.socket, ip: str, requested_port: int) -> None:
        """ Bind socket to provided ip address and port. If port not available incrementally search for an open port. """

        port = requested_port
        while True:
            try:
                s.bind((ip, port))
                print('Socket bound on port', port)
                break
            except socket.error as e:
                print('Socket failed to bind on port', port)
                if e.errno == errno.EADDRINUSE and port < requested_port + TCPServer.MAX_BIND_TRIES:
                    port += 1
                else: raise

    def close_socket(self, s: socket.socket) -> None:
        """ Close the provided socket, freeing up the port. """

        self.sel.unregister(s)
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        print('Socket closed')
