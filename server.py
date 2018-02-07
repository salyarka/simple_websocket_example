import socket
import select


def shake_hands():
    """Shake hands with client by websocket rules.
    """


s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
s_sock.bind(('127.0.0.1', 59599))
# by default is sets to socket.SOMAXCONN
s_sock.listen()
# set non-blocking mode
s_sock.setblocking(0)
ep = select.epoll()
# register event for connection to server socket
ep.register(s_sock.fileno(), select.EPOLLIN)
connections = {}

while True:
    events = ep.poll()
    for fd, ev in events:
        if fd == s_sock.fileno():
            c_sock, c_addr = s_sock.accept()
            print('client connected, addr: %s' % (c_addr,))
            c_sock.setblocking(0)
            ep.register(c_sock.fileno(), select.EPOLLIN)
            connections[c_sock.fileno()] = c_sock
        elif ev and select.EPOLLHUP:
            # client disonnected
            print('client disconnected')
            ep.unregister(fd)
            connections[fd].close()
            del connections[fd]
        elif ev and select.EPOLLIN:
            # data arrived from client
            print('reecived %s' % connections[fd].recv(1024))
        elif ev and select.EPOLLOUT:
            # it is able to send data to client
            print('epollout')

