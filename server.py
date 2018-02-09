import socket
import select


ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
ss.bind(('127.0.0.1', 59599))
# by default is sets to socket.SOMAXCONN
ss.listen()
# set non-blocking mode
ss.setblocking(0)
ep = select.epoll()
# register event for connection to server socket
ep.register(ss.fileno(), select.EPOLLIN)
conns = {}

def shake_hands():
    """Shake hands with client by websocket rules.
    """


def close_conn(fd):
    """Close connection, unregister from events
    and del connection from cons
    """
    ep.unregister(fd)
    conns[fd].close()
    del conns[fd]

try:
    while True:
        events = ep.poll()
        for fd, ev in events:
            if fd == ss.fileno():
                cs, addr = ss.accept()
                print('client connected, addr: %s' % (addr,))
                cs.setblocking(0)
                ep.register(cs.fileno(), select.EPOLLIN)
                conns[cs.fileno()] = cs
            elif ev & (select.EPOLLERR | select.EPOLLHUP):
                # hang up or error  happened
                close_conn(fd)
            elif ev & select.EPOLLIN:
                # data arrived from client
                data = conns[fd].recv(1024)
                print('recived %s' % data)
                if not data:
                    print('client disconnected')
                    close_conn(fd)
finally:
    ep.unregister(ss.fileno())
    ep.close()
    ss.close()

