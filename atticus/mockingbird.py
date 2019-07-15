import errno
import selectors
import socket
from multiprocessing import Value
from typing import Optional, Tuple

BUFFER_SIZE = 1024
MAX_BIND_TRIES = 100

SELECT_TIMEOUT = 0.1
sel = selectors.DefaultSelector()

def mock(stop: Value) -> None:
    parse()

    ip = "127.0.0.1"
    requested_port = 42826

    s = create_socket()
    bind_socket(s, ip, requested_port)
    s.listen(10)
    

    while not stop.value:
        events = sel.select(SELECT_TIMEOUT)
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)
    
    close_socket(s)
    print("Stopping the mockingbird")

def parse():
    pass

def socket_receive(conn: socket.socket) -> None:
    print("Receiving data")
    data = conn.recv(BUFFER_SIZE)
    if data:
        print("Received data:", data)
        conn.send(data)
    else:
        print("Client disconnected")
        sel.unregister(conn)

def create_socket() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(False)
    sel.register(s, selectors.EVENT_READ, accept_client)
    return s

def accept_client(s:  socket) -> None:
    print("Accepting client")
    conn, addr = s.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, socket_receive)  

def bind_socket(s: socket.socket, ip: str, requested_port: int) -> None:
    # Increment ports until successfully binding to a port
    port = requested_port
    while True:
        try:
            print('Socket binding on port', port)
            s.bind((ip, port))
            print('Socket bound on port', port)
            break
        except socket.error as e:
            print('Socket failed to bind on port', port)
            if e.errno == errno.EADDRINUSE and port < requested_port + MAX_BIND_TRIES:
                port += 1
            else: raise

def close_socket(s: socket.socket) -> None:
    print('Socket closing on port')
    sel.unregister(s)
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    print('Socket closed on port')
