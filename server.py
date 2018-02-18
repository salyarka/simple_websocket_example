import socket
import select

from client import Client
from ws import get_key, prepare_data, decode_frame, BAD_REQUEST


ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
ss.bind(('127.0.0.1', 59599))
# by default is sets to socket.SOMAXCONN
ss.listen()
# set non-blocking mode
ss.setblocking(0)
ep = select.epoll()
# register event for connection to server socket
ep.register(ss.fileno(), select.EPOLLIN)
clients = {}


def close_conn(file_descriptor):
    """Close connection, unregister from events
    and del client object.

    :param file_descriptor: is used as key for clients dictionary and for
        unregister from epoll
    """
    ep.unregister(file_descriptor)
    clients[file_descriptor].disconnect()
    del clients[file_descriptor]

# TODO: closing connections when clietn os closed websocket
try:
    while True:
        events = ep.poll()
        for fd, ev in events:
            if fd == ss.fileno():
                cs, addr = ss.accept()
                print('client connected, addr: %s' % (addr,))
                cs.setblocking(0)
                ep.register(cs.fileno(), select.EPOLLIN)
                clients[cs.fileno()] = Client(cs)

            elif ev & (select.EPOLLERR | select.EPOLLHUP):
                # hang up or error  happened
                close_conn(fd)

            elif ev & select.EPOLLIN:
                # data arrived from client
                data = clients[fd].recv()
                print('received %s' % data)
                if not data:
                    print('client disconnected')
                    close_conn(fd)
                # make handshake
                if not clients[fd].handshake:
                    k = get_key(data)
                    if k is None:
                        print('!!! bad request')
                        clients[fd].send(BAD_REQUEST)
                        close_conn(fd)
                    else:
                        # TODO: redesign code, client class should nothing know
                        # about websocket
                        clients[fd].shake_hands(k)
                else:
                    # TODO: redesign decode_frame and prepare_data
                    data = decode_frame(bytearray(data))
                    data = prepare_data(data)
                    clients[fd].last_message = data
                    ep.modify(fd, select.EPOLLOUT)

            elif ev & select.EPOLLOUT:
                clients[fd].send(clients[fd].last_message)
                ep.modify(fd, select.EPOLLIN)

finally:
    ep.unregister(ss.fileno())
    ep.close()
    ss.close()

