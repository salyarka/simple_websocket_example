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
    """
    key += WS_MAGIC_STRING
    resp_key = base64.standard_b64encode(
        hashlib.sha1(key).digest()
    )
    return HANDSHAKE_RESPONSE % resp_key


def get_key(request):
    """Getting websoket key from request.

    :param data: http request
    """
    # TODO: redesign function, go away from cycle throw headers
    headers = request.split(b'\r\n')
    if b'Connection: Upgrade' in headers and \
                    b'Upgrade: websocket' in headers:
        print('!!! websocket upgrade request')
        for h in headers:
            if b'Sec-WebSocket-Key' in h:
                return h.split(b' ')[1]
                break


def decode_frame(frame):
    """Decodes frame, considered only opcode for closing connection.

    :param frame: websocket frame from client
    """
    frame = bytearray(frame)
    fin_and_opcode = frame[0]
    if fin_and_opcode & 0xf == 0x8:
        # opcode 8 - Connection Close Frame
        return
    payload_len = frame[1] - 128

    mask = frame[2:6]
    encrypted_payload = frame[6:6 + payload_len]

    payload = bytearray(
        [
            encrypted_payload[i] ^ mask[i % 4]
            for i in range(payload_len)
        ]
    )

    return payload


def prepare_data(payload):
    # setting fin to 1 and opcode to 0x1
    frame = [129]
    frame += [len(payload)]
    result_frame = bytearray(frame) + payload

    return result_frame

