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
conns = {}

def shake_hands(key, conn):
    """Shake hands with client by websocket rules.
    """
    # calculating response as per protocol RFC
    key = key + WS_MAGIC_STRING
    resp_key = base64.standard_b64encode(
        hashlib.sha1(key).digest()
    )

    resp = b'%s\r\n%s\r\n%s\r\n%s %s\r\n\r\n' % (
        b'HTTP/1.1 101 Switching Protocols',
        b'Upgrade: websocket',
        b'Connection: Upgrade',
        b'Sec-WebSocket-Accept:',
        resp_key
    )

    conn.send(resp)


def close_conn(fd):
    """Close connection, unregister from events
    and del connection from cons
    """
    ep.unregister(fd)
    conns[fd].close()
    del conns[fd]


def decode_frame(frame):
    opcode_and_fin = frame[0]

    # assuming it's masked, hence removing the mask bit(MSB) to get len.
    # also assuming len is <125
    payload_len = frame[1] - 128

    mask = frame[2:6]
    encrypted_payload = frame[6: 6+payload_len]

    payload = bytearray(
        [
            encrypted_payload[i] ^ mask[i%4]
            for i in range(payload_len)
        ]
    )

    return payload


def send_frame(payload, conn):
    # setting fin to 1 and opcpde to 0x1
    frame = [129]
    # adding len. no masking hence not doing +128
    frame += [len(payload)]
    # adding payload
    frame_to_send = bytearray(frame) + payload

    conn.send(frame_to_send)


class Client:
    pass

# TODO: distinguish connection that are upgraded (make Client class???)
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
                # make handshake
                headers = data.split(b'\r\n')
                if b'Connection: Upgrade' in data and \
                        b'Upgrade: websocket' in data:
                    print('!!! websocket upgrade request')
                    for h in headers:
                        if b'Sec-WebSocket-Key' in h:
                            key = h.split(b' ')[1]
                            break
                    shake_hands(key, conns[fd])
                else:
                    print('!!! bad request')
                    conns[fd].send(
                        b'%s\r\n%s\r\n%s\r\n\r\n%s' % (
                        b'HTTP/1.1 400 Bad Request',
                        b'Content-Type: text/plain',
                        b'Connection: close',
                        b'Incorrect request'
                        )
                    )
                    close_conn(fd)
finally:
    ep.unregister(ss.fileno())
    ep.close()
    ss.close()

