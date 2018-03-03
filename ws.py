import hashlib
import base64

WS_MAGIC_STRING = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

HANDSHAKE_RESPONSE = b'HTTP/1.1 101 Switching Protocols\r\n' \
       b'Upgrade: websocket\r\n' \
       b'Connection: Upgrade\r\n' \
       b'Sec-WebSocket-Accept: %s\r\n\r\n'

BAD_REQUEST = b'HTTP/1.1 400 Bad Request\r\n' \
              b'Content-Type: text/plain\r\n' \
              b'Connection: close\r\n\r\n'


def make_handshake_response(key):
    """Creates handshake response for client.

    :param key: websocket key
    :return: response with key
    """
    key += WS_MAGIC_STRING
    resp_key = base64.standard_b64encode(
        hashlib.sha1(key).digest()
    )
    return HANDSHAKE_RESPONSE % resp_key


def get_key(request):
    """Getting websoket key from request. If request does not contain websocket
    headers returns None.

    :param data: http request
    :return: websocket key or None
    """
    # TODO: redesign function, go away from cycle throw headers
    headers = request.split(b'\r\n')
    if b'Connection: Upgrade' in headers and \
                    b'Upgrade: websocket' in headers:
        print('!!! websocket upgrade request')
        for h in headers:
            if b'Sec-WebSocket-Key' in h:
                return h.split(b' ')[1]


def decode_frame(frame):
    """Decodes frame, considered only opcode for closing connection. If frame
    contains close opcode returns None.

    :param frame: websocket frame from client
    :return: decoded frame or None
    """
    frame = bytearray(frame)
    fin_and_opcode = frame[0]

    if fin_and_opcode & 0xf == 0x8:
        # opcode 8 - Connection Close Frame
        return

    payload_len = frame[1] - 128
    mask = frame[2:6]
    encrypted_payload = frame[6:6 + payload_len]

    return  bytearray(
        [
            encrypted_payload[i] ^ mask[i % 4]
            for i in range(payload_len)
        ]
    )


def prepare_data(payload):
    """Sets opcode to 0x1, fin to 1
    
    :param payload: data for client
    :return: data ready to send for client 
    """
    # setting fin to 1 and opcode to 0x1
    frame = [129]
    frame += [len(payload)]
    return bytearray(frame) + payload
