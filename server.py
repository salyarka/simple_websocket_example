import socket
import select


def shake_hands():
    """Shake hands with client by websocket rules.
    """


s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
s_sock.bind(('127.0.0.1', 59599))
# see man page for listen
s_sock.listen(128)
# set non-blocking mode
s_sock.setblocking(0)
ep = select.epoll()
# register event for connection to server socket
ep.register(ep.fileno(), select.EPOLLIN)

while True:
    events = ep.poll(1)
    for fd, ev in events:
        if fd == s_sock.fileno():
            c_sock, c_addr = s_sock.accept()
            print('client connected, addr: %s' % (c_addr,))
        elif ev and select.EPOLLIN:
            # data arrived from client
            pass
        elif ev and select.EPOLLOUT:
            # it is able to send data to client
            pass
        elif event and select.EPOLLHUP:
            # client disonnected
            pass
    #while True:
    #    data = c_sock.recv(1024)
    #    if not data:
    #        print('client disconnected')
    #        break
    #    c_sock.sendall(b'echo: %s' % data)
    #c_sock.close()

