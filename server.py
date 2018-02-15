import socket
import select
import hashlib
import base64


WS_MAGIC_STRING = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

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


def shake_hands(key, client):
    """Shake hands with client by websocket rules.

    :param key: websocket key
    :param client: client object
    """
    # calculating response as per protocol RFC
    key += WS_MAGIC_STRING
    resp_key = base64.standard_b64encode(
        hashlib.sha1(key).digest()
    )

    resp = b'HTTP/1.1 101 Switching Protocols\r\n' \
           b'Upgrade: websocket\r\n' \
           b'Connection: Upgrade\r\n' \
           b'Sec-WebSocket-Accept: %s\r\n\r\n' % resp_key

    client.cs.send(resp)
    client.handshake = True


def close_conn(file_descriptor):
    """Close connection, unregister from events
    and del connection from cons

    :param file_descriptor: is used as key for clients dictionary and for
        unregister from epoll
    """
    ep.unregister(file_descriptor)
    clients[file_descriptor].cs.close()
    del clients[file_descriptor]


def decode_frame(frame):
    opcode_and_fin = frame[0]
    print('!!! opcode_and_fin', opcode_and_fin)

    # assuming it's masked, hence removing the mask bit(MSB) to get len.
    # also assuming len is <125
    payload_len = frame[1] - 128

    mask = frame[2:6]
    encrypted_payload = frame[6: 6+payload_len]

    payload = bytearray(
        [
            encrypted_payload[i] ^ mask[i % 4]
            for i in range(payload_len)
        ]
    )

    return payload


def send_frame(payload, client):
    # setting fin to 1 and opcode to 0x1
    frame = [129]
    # adding len. no masking hence not doing +128
    frame += [len(payload)]
    # adding payload
    frame_to_send = bytearray(frame) + payload

    client.cs.send(frame_to_send)


class Client:
    # need status (in connecting, after handshake, online ...)
    def __init__(self, client_socket):
        self.handshake = False
        self.cs = client_socket


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
                data = clients[fd].cs.recv(1024)
                print('received %s' % data)
                if not data:
                    print('client disconnected')
                    close_conn(fd)
                # make handshake
                if not clients[fd].handshake:
                    headers = data.split(b'\r\n')
                    if b'Connection: Upgrade' in headers and \
                            b'Upgrade: websocket' in headers:
                        print('!!! websocket upgrade request')
                        for h in headers:
                            if b'Sec-WebSocket-Key' in h:
                                shake_hands(h.split(b' ')[1], clients[fd])
                                break
                        else:
                            print(
                                '!!! bad request, no websocket key in headers'
                            )
                            bad_request = b'HTTP/1.1 400 Bad Request\r\n' \
                                          b'Content-Type: text/plain\r\n' \
                                          b'Connection: close\r\n\r\n'
                            clients[fd].cs.send(bad_request)
                            close_conn(fd)
                    else:
                        print('!!! bad request')
                        bad_request = b'HTTP/1.1 400 Bad Request\r\n' \
                                      b'Content-Type: text/plain\r\n' \
                                      b'Connection: close\r\n\r\n'
                        clients[fd].cs.send(bad_request)
                        close_conn(fd)
                else:
                    data = decode_frame(bytearray(data))
                    send_frame(data, clients[fd])
finally:
    ep.unregister(ss.fileno())
    ep.close()
    ss.close()
